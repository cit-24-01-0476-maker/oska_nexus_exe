import json
import time
from typing import Dict, Any, List
from windows.apps import launch_application, open_url
from windows.audio import set_system_volume
from storage.database import get_connection, log_audit
from storage.reminders import create_reminder

class RoutineRunner:
    def __init__(self, tts_engine=None, notifier=None):
        self.tts = tts_engine
        self.notifier = notifier

    def run_routine(self, routine_id: str) -> Dict[str, Any]:
        conn = get_connection()
        row = conn.execute("SELECT * FROM routines WHERE id = ? AND enabled = 1", (routine_id,)).fetchone()
        conn.close()

        if not row:
            return {
                "status": "FAILED",
                "response": f"Routine '{routine_id}' not found or disabled.",
                "spoken_response": "Routine not found."
            }

        name = row["name"]
        actions = json.loads(row["actions_json"])
        executed_steps = []
        all_success = True

        for step in actions:
            step_type = step.get("type")
            target = step.get("target", "")
            label = step.get("label", step_type)

            try:
                if step_type == "open_app":
                    ok, _ = launch_application(target)
                    executed_steps.append({"label": label, "status": "SUCCESS" if ok else "FAILED"})
                    if not ok: all_success = False

                elif step_type == "open_url":
                    ok, _ = open_url(target)
                    executed_steps.append({"label": label, "status": "SUCCESS" if ok else "FAILED"})
                    if not ok: all_success = False

                elif step_type == "set_volume":
                    try:
                        lvl = int(target)
                        ok = set_system_volume(lvl)
                        executed_steps.append({"label": label, "status": "SUCCESS" if ok else "FAILED"})
                        if not ok: all_success = False
                    except Exception:
                        all_success = False
                        executed_steps.append({"label": label, "status": "FAILED"})

                elif step_type == "speak_time":
                    from datetime import datetime
                    now_str = datetime.now().strftime("%I:%M %p")
                    if self.tts: self.tts.speak(f"It is {now_str}.")
                    executed_steps.append({"label": f"Announced time: {now_str}", "status": "SUCCESS"})

                elif step_type == "timer":
                    minutes = float(target)
                    if not 0 < minutes <= 10080:
                        raise ValueError('Timer must be between 0 and 10080 minutes.')
                    create_reminder(f'{name}: focus timer finished', time.time() + minutes * 60)
                    executed_steps.append({"label": f'Timer: {minutes:g} minutes', "status": "SUCCESS"})

                elif step_type == "notify":
                    if self.notifier: self.notifier(name, target)
                    if self.tts: self.tts.speak(target)
                    executed_steps.append({"label": target, "status": "SUCCESS"})

                else:
                    all_success = False
                    executed_steps.append({"label": f"Unsupported action: {step_type}", "status": "FAILED"})

                # Small delay between actions for window management smoothness
                time.sleep(0.3)
            except Exception as e:
                executed_steps.append({"label": f"{label} ({e})", "status": "FAILED"})
                all_success = False

        status_str = "SUCCESS" if all_success else "PARTIAL_SUCCESS"
        log_audit("RUN_ROUTINE", f"{name} ({routine_id}): {len(executed_steps)} steps", status_str)

        return {
            "status": status_str,
            "response": f"{name}: {sum(s['status'] == 'SUCCESS' for s in executed_steps)}/{len(executed_steps)} actions completed.",
            "spoken_response": f"{name} completed." if all_success else f"{name} finished with failed actions. Check the result.",
            "data": {
                "routine_id": routine_id,
                "name": name,
                "steps": executed_steps
            }
        }
