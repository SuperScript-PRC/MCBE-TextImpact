def translate_tellraw(
    jsonc: dict, *, selectors_sub: dict[str, str], scores_sub: dict[str, dict[str, int]]
):
    rawtext = jsonc["rawtext"]
    if not isinstance(rawtext, list):
        raise ValueError(
            f"Invalid rawtext param type; need list, got {type(rawtext).__name__}"
        )
    for i, element in enumerate(rawtext.copy()):
        if "score" in element:
            score = element["score"]
            name = score["name"]
            objective = score["objective"]
            if (scb_data := scores_sub.get(objective)) and name in scb_data:
                rawtext[i] = {"text": str(scb_data[name])}
            else:
                rawtext[i] = {"text": ""}
        elif "selector" in element:
            if element["selector"] in selectors_sub:
                rawtext[i] = {"text": selectors_sub[element["selector"]]}
            else:
                rawtext[i] = {"text": ""}
        elif "translate" in element:
            translates = element["translate"]

    return {"rawtext": rawtext}
