"""Intervalo de Wilson 95% para proporciones binomiales."""
import math

def wilson(success: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return (0.0,0.0)
    p = success / total
    denom = 1 + z*z/total
    center = (p+z*z/(2*total)) / denom
    rad = z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/denom
    return max(0.0, center-rad), min(1.0,center+rad)
