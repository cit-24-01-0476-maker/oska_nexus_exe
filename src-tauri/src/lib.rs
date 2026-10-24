use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Emitter, Manager, WindowEvent,
};
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut};

static SIDECAR_CHILD: Mutex<Option<Child>> = Mutex::new(None);

fn spawn_python_backend(app: &AppHandle) {
    let resource_dir = app.path().resource_dir().ok();
    std::thread::spawn(move || {
        let bundled = resource_dir.as_ref().map(|p| p.join("backend").join("oska-backend.exe"));
        let mut cmd = if bundled.as_ref().is_some_and(|p| p.exists()) {
            let b = bundled.unwrap();
            let mut c = Command::new(&b);
            if let Some(parent) = b.parent() {
                c.current_dir(parent);
            }
            c
        } else {
            let exe_dir = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.to_path_buf()));
            let manifest_parent = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().unwrap().to_path_buf();
            
            let candidate_pythons = [
                manifest_parent.join("python-backend").join("venv").join("Scripts").join("python.exe"),
                manifest_parent.join(".venv").join("Scripts").join("python.exe"),
                std::path::PathBuf::from("E:\\OSKA-NEXUS-DESKTOP\\python-backend\\venv\\Scripts\\python.exe"),
                std::path::PathBuf::from("E:\\OSKA-NEXUS-DESKTOP\\.venv\\Scripts\\python.exe"),
                exe_dir.as_ref().map(|d| d.join("..").join("..").join("..").join("python-backend").join("venv").join("Scripts").join("python.exe")).unwrap_or_default(),
            ];

            let python_bin = candidate_pythons.iter()
                .find(|p| p.exists())
                .cloned()
                .unwrap_or_else(|| "python".into());

            let candidate_mains = [
                manifest_parent.join("python-backend").join("main.py"),
                std::path::PathBuf::from("E:\\OSKA-NEXUS-DESKTOP\\python-backend\\main.py"),
                exe_dir.as_ref().map(|d| d.join("..").join("..").join("..").join("python-backend").join("main.py")).unwrap_or_default(),
            ];

            let main_script = candidate_mains.iter()
                .find(|p| p.exists())
                .cloned()
                .unwrap_or_else(|| manifest_parent.join("python-backend").join("main.py"));

            let mut command = Command::new(python_bin);
            command.arg(&main_script);
            if let Some(parent) = main_script.parent() {
                command.current_dir(parent);
            }
            command
        };

        cmd.env("PYTHONIOENCODING", "utf-8").env("PYTHONUTF8", "1");
        #[cfg(windows)] {
            use std::os::windows::process::CommandExt;
            cmd.creation_flags(0x08000000);
        }
        // Keep backend diagnostics available when launched without a console.
        if let Some(data) = std::env::var_os("LOCALAPPDATA") {
            let dir = std::path::PathBuf::from(data).join("OSKA NEXUS");
            let _ = std::fs::create_dir_all(&dir);
            if let Ok(log) = std::fs::OpenOptions::new().create(true).append(true).open(dir.join("backend.log")) {
                if let Ok(copy) = log.try_clone() { cmd.stdout(copy); }
                cmd.stderr(log);
            }
        }
        match cmd.spawn() {
            Ok(child) => { *SIDECAR_CHILD.lock().unwrap() = Some(child); }
            Err(error) => eprintln!("Failed to start OSKA backend: {error}"),
        }
    });
}

fn kill_python_backend() {
    let mut lock = SIDECAR_CHILD.lock().unwrap();
    if let Some(mut child) = lock.take() {
        println!("[Tauri] Terminating Python backend PID: {}", child.id());
        let _ = child.kill();
        let _ = child.wait();
    }
}

#[tauri::command]
fn show_floating_assistant(app: AppHandle) -> Result<(), String> {
    open_overlay(app, true)
}

#[tauri::command]
fn reveal_floating_assistant(app: AppHandle) -> Result<(), String> {
    open_overlay(app, false)
}

fn open_overlay(app: AppHandle, activate: bool) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("floating") {
        if let Ok(Some(monitor)) = window.current_monitor() {
            let screen_size = monitor.size();
            let screen_w = screen_size.width as i32;
            let screen_h = screen_size.height as i32;
            let win_w = 440;
            let win_h = 260;
            let x = (screen_w - win_w) / 2;
            let y = screen_h - win_h - 90;
            let _ = window.set_position(tauri::Position::Physical(tauri::PhysicalPosition { x, y }));
        }
        let _ = window.show();
        let _ = window.set_focus();
        if activate { let _ = window.emit("activated", ()); }
    }
    Ok(())
}

#[tauri::command]
fn hide_floating_assistant(app: AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("floating") {
        let _ = window.hide();
    }
    Ok(())
}

#[tauri::command]
fn quit_app(app: AppHandle) {
    kill_python_backend();
    app.exit(0);
}

#[tauri::command]
fn apply_desktop_settings(app: AppHandle, settings: std::collections::HashMap<String, String>) -> Result<(), String> {
    let path = app.path().app_data_dir().map_err(|e| e.to_string())?.join("desktop-settings.json");
    let mut stored: std::collections::HashMap<String, String> = std::fs::read(&path).ok().and_then(|v| serde_json::from_slice(&v).ok()).unwrap_or_default();
    for key in ["minimize_to_tray", "start_with_windows"] {
        if let Some(value) = settings.get(key) { stored.insert(key.to_string(), value.clone()); }
    }
    #[cfg(windows)]
    if let Some(enabled) = settings.get("start_with_windows") {
        use std::os::windows::process::CommandExt;
        let mut command = Command::new("reg.exe");
        command.creation_flags(0x08000000);
        let key = "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run";
        if enabled == "true" {
            let exe = std::env::current_exe().map_err(|e| e.to_string())?;
            command.args(["add", key, "/v", "OSKA NEXUS", "/t", "REG_SZ", "/d", &format!("\"{}\" --background", exe.display()), "/f"]);
            let status = command.status().map_err(|e| e.to_string())?;
            if !status.success() { return Err("Could not enable startup at Windows login.".into()); }
        } else {
            command.args(["delete", key, "/v", "OSKA NEXUS", "/f"]);
            let _ = command.output();
        }
    }
    std::fs::create_dir_all(path.parent().unwrap()).map_err(|e| e.to_string())?;
    std::fs::write(path, serde_json::to_vec(&stored).map_err(|e| e.to_string())?).map_err(|e| e.to_string())
}

#[tauri::command]
fn notify_user(app: AppHandle, title: String, body: String) -> Result<(), String> {
    use tauri_plugin_notification::NotificationExt;
    app.notification().builder().title(title).body(body).show().map_err(|e| e.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .invoke_handler(tauri::generate_handler![
            show_floating_assistant,
            reveal_floating_assistant,
            apply_desktop_settings,
            notify_user,
            hide_floating_assistant,
            quit_app
        ])
        .setup(|app| {
            let handle = app.handle();
            if std::env::args().any(|a| a == "--background") {
                if let Some(window) = app.get_webview_window("main") { let _ = window.hide(); }
            }

            // 1. Spawn backend sidecar
            spawn_python_backend(handle);

            // 2. Setup System Tray Menu
            let open_item = MenuItem::with_id(handle, "open", "Open OSKA NEXUS", true, None::<&str>)?;
            let activate_item = MenuItem::with_id(handle, "activate", "Activate Assistant", true, None::<&str>)?;
            let sep = MenuItem::with_id(handle, "sep1", "---", false, None::<&str>)?;
            let quit_item = MenuItem::with_id(handle, "quit", "Quit Completely", true, None::<&str>)?;

            let tray_menu = Menu::with_items(handle, &[&open_item, &activate_item, &sep, &quit_item])?;

            let _tray = TrayIconBuilder::new()
                .icon(app.default_window_icon().expect("OSKA bundled window icon").clone())
                .menu(&tray_menu)
                .tooltip("OSKA NEXUS - Personal Desktop Intelligence")
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "open" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    "activate" => {
                        let _ = show_floating_assistant(app.clone());
                    }
                    "quit" => {
                        quit_app(app.clone());
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            if let Ok(is_visible) = window.is_visible() {
                                if is_visible {
                                    let _ = window.hide();
                                } else {
                                    let _ = window.show();
                                    let _ = window.set_focus();
                                }
                            }
                        }
                    }
                })
                .build(app)?;

            // 3. Register Global Keyboard Shortcut (Ctrl+Shift+Space)
            let shortcut_handle = handle.clone();
            let _ = handle.plugin(
                tauri_plugin_global_shortcut::Builder::new()
                    .with_handler(move |_app, _shortcut, event| {
                        if event.state() == tauri_plugin_global_shortcut::ShortcutState::Pressed {
                            let _ = show_floating_assistant(shortcut_handle.clone());
                        }
                    })
                    .build(),
            );

            if let Ok(shortcut) = "Ctrl+Shift+Space".parse::<Shortcut>() {
                let _ = handle.global_shortcut().register(shortcut);
            }

            // 4. Handle Window Close requested (hide to tray instead of termination)
            let main_win = app.get_webview_window("main");
            if let Some(win) = main_win {
                let win_clone = win.clone();
                let close_handle = handle.clone();
                win.on_window_event(move |event| {
                    if let WindowEvent::CloseRequested { api, .. } = event {
                        let minimize = close_handle.path().app_data_dir().ok()
                            .and_then(|p| std::fs::read(p.join("desktop-settings.json")).ok())
                            .and_then(|b| serde_json::from_slice::<serde_json::Value>(&b).ok())
                            .and_then(|v| v.get("minimize_to_tray").and_then(|v| v.as_str()).map(|v| v != "false"))
                            .unwrap_or(true);
                        if minimize { api.prevent_close(); let _ = win_clone.hide(); }
                        else { kill_python_backend(); close_handle.exit(0); }
                    }
                });
            }

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|_app_handle, event| {
            if let tauri::RunEvent::Exit = event {
                kill_python_backend();
            }
        });
}
