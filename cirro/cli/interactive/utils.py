import questionary
from questionary import prompt


class InputError(Exception):
    """Errors detected from user input"""
    pass


def prompt_wrapper(questions):
    answers = prompt(questions)
    # Prompt catches KeyboardInterrupt and sends back an empty dictionary
    # We want to catch this exception
    if len(answers) == 0:
        raise KeyboardInterrupt()
    return answers


def type_validator(t, v):
    """Return a boolean indicating whether `v` can be cast to `t(v)` without raising a ValueError."""
    try:
        t(v)
        return True
    except ValueError:
        return False


def ask(fname, msg, validate_type=None, output_f=None, **kwargs) -> str:
    """Wrap questionary functions to catch escapes and exit gracefully."""

    # Get the questionary function
    questionary_f = questionary.__dict__.get(fname)

    # Make sure that the function exists
    assert questionary_f is not None, f"No such questionary function: {fname}"

    if fname == "select":
        kwargs["use_shortcuts"] = True

    if validate_type is not None:
        kwargs["validate"] = lambda v: type_validator(validate_type, v)

    # The default value must be a string
    if kwargs.get("default") is not None:
        kwargs["default"] = str(kwargs["default"])

    if kwargs.get("required"):
        del kwargs["required"]
        kwargs["validate"] = lambda val: len(val.strip()) > 0 or "This field is required"

    # Add a spacer line before asking the question
    print("")

    # Get the response
    resp = questionary_f(msg, **kwargs).ask()

    # If the user escaped the question
    if resp is None:
        raise KeyboardInterrupt()

    # If an output transformation function was defined
    if output_f is not None:

        # Call the function
        resp = output_f(resp)

    # Otherwise
    return resp


def ask_yes_no(msg):
    return ask("select", msg, choices=["Yes", "No"]) == "Yes"


def get_id_from_name(items, name_or_id: str) -> str:
    return get_item_from_name_or_id(items, name_or_id).id


def get_item_from_name_or_id(items, name_or_id: str):
    matched = next((p for p in items if p.id == name_or_id), None)
    if matched:
        return matched
    return next(p for p in items if p.name == name_or_id)
