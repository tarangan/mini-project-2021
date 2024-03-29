#!/usr/bin/env python3
"""Entry point for example chatbot application using Infermedica API.



Example:
    To start the application simply type::

        $ python3 chat.py APP_ID:APP_KEY

    where `APP_ID` and `APP_KEY` are Application Id and Application Key from
    your Infermedica account respectively.

Note:
    If you don't have an Infermedica account, please register at
    https://developer.infermedica.com.

"""
import argparse
import uuid

import conversation
import apiaccess

def get_auth_string(auth_or_path):
    """Retrieves authentication string from string or file.

    Args:
        auth_or_path (str): Authentication string or path to file containing it

    Returns:
        str: Authentication string.

    """
    if ':' in auth_or_path:
        return auth_or_path
    try:
        with open(auth_or_path) as stream:
            content = stream.read()
            content = content.strip()
            if ":" in content:
                return content
    except FileNotFoundError:
        pass
    raise ValueError(auth_or_path)


def new_case_id():
    return uuid.uuid4().hex


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("auth",
                        help="authentication string for Infermedica API: "
                             "APP_ID:APP_KEY or path to file containing it.")
    parser.add_argument("--model",
                        help="use non-standard Infermedica model/language, "
                             "e.g. infermedica-es")
    args = parser.parse_args()
    return args


def run():
    """Runs the main application."""
    args = parse_args()
    auth_string = get_auth_string(args.auth)
    case_id = new_case_id()

    # Read patient's age and sex; required by /diagnosis endpoint.
    # Alternatively, this could be done after learning patient's complaints
    age, sex = conversation.read_age_sex()
    print(f"Ok, {age} year old {sex}.")
    age = {'value':  age, 'unit': 'year'}

    # Query for all observation names and store them.
    naming = apiaccess.get_observation_names(age, auth_string, case_id, args.model)

    # Read patient's complaints by using /parse endpoint.
    mentions = conversation.read_complaints(age, sex, auth_string, case_id, args.model)

    # Keep asking diagnostic questions until stop condition is met.
    evidence = apiaccess.mentions_to_evidence(mentions)
    evidence, diagnoses, triage = conversation.conduct_interview(evidence, age,
                                                                 sex, case_id,
                                                                 auth_string,
                                                                 args.model)

    # summary.
    apiaccess.name_evidence(evidence, naming)

    # Print out all that we've learnt about the case and finish.
    print()
    conversation.summarise_all_evidence(evidence)
    conversation.summarise_diagnoses(diagnoses)
    conversation.summarise_triage(triage)
    apiaccess.call_parse(case_id)


if __name__ == "__main__":
    run()
