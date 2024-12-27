from typing import Dict, Optional

class NotationHelper:
    """Helper functions for musical notation"""
    
    @staticmethod
    def format_duration(beats: float) -> str:
        """Format duration in beats to notation string"""
        if beats == 1.0:
            return ""
        elif beats == 0.5:
            return "1/2"
        elif beats == 0.25:
            return "1/4"
        else:
            return str(beats)
    
    @staticmethod
    def format_technique(technique: str) -> str:
        """Format technique as tab notation symbol"""
        technique_map = {
            "hammer-on": "h",
            "pull-off": "p",
            "bend": "b",
            "slide": "/",
            "tap": "t",
            "harmonic": "*",
            "palm-mute": "x"
        }
        return technique_map.get(technique, "")