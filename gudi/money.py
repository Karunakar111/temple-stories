"""Exact credit arithmetic. Credits are stored as integer milli-credits (6.25 -> 6250)."""
from decimal import ROUND_HALF_UP, Decimal

SCALE = 1000


def to_milli(value):
    d = Decimal(str(value))
    m = d * SCALE
    if m != m.to_integral_value():
        raise ValueError(f"{value} has more precision than 0.001 credit")
    return int(m)


def fmt(milli):
    if milli is None:
        return "unset"
    d = (Decimal(milli) / SCALE).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP).normalize()
    s = format(d, "f")
    return s
