def build_note(differing_names: int, differing_weights: int) -> str:
    if differing_names == 0 and differing_weights == 0:
        return "BT und RUN sind im Toleranzbereich."
    if differing_names > 0 and differing_weights == 0:
        return "Namensabweichungen gefunden."
    if differing_names == 0 and differing_weights > 0:
        return "Gewichtsabweichungen gefunden."
    return "Namens- und Gewichtsabweichungen gefunden."