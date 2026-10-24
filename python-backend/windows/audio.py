def set_system_volume(level: int) -> bool:
    """Sets system master volume between 0 and 100."""
    try:
        from pycaw.pycaw import AudioUtilities
        sp = AudioUtilities.GetSpeakers()
        level = max(0, min(100, level))
        if hasattr(sp, "EndpointVolume"):
            sp.EndpointVolume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return True
        elif hasattr(sp, "volume_percent"):
            sp.volume_percent = level
            return True
        return False
    except Exception as e:
        print(f"[Audio] Error setting volume: {e}")
        return False

def get_system_volume() -> int:
    """Returns system master volume between 0 and 100."""
    try:
        from pycaw.pycaw import AudioUtilities
        sp = AudioUtilities.GetSpeakers()
        if hasattr(sp, "volume_percent"):
            return int(round(sp.volume_percent))
        if hasattr(sp, "EndpointVolume"):
            scalar = sp.EndpointVolume.GetMasterVolumeLevelScalar()
            return int(round(scalar * 100))
        return 50
    except Exception as e:
        print(f"[Audio] Error getting volume: {e}")
        return 50

def set_system_mute(mute: bool) -> bool:
    """Mutes or unmutes system audio."""
    try:
        from pycaw.pycaw import AudioUtilities
        sp = AudioUtilities.GetSpeakers()
        if hasattr(sp, "EndpointVolume"):
            sp.EndpointVolume.SetMute(1 if mute else 0, None)
            return True
        return False
    except Exception as e:
        print(f"[Audio] Error toggling mute: {e}")
        return False
