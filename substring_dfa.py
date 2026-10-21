# DFA Pattern Detection Simulator

def build_dfa(pattern):
    # Stores the length of the pattern, and an empty dictionary
    pattern_length = len(pattern)
    transitions = {}

    # Create a transition for every state and input symbol.
    for state in range(pattern_length + 1):
        transitions[state] = {}

        for symbol in ("0", "1"):

            # Once the pattern is found, stay in the final state.
            if state == pattern_length:
                next_state = pattern_length

            else:
                # Add the new symbol to the matched pattern prefix.
                candidate = pattern[:state] + symbol

                # Find the longest pattern prefix that matches
                # the end of the candidate.
                next_state = 0

                for length in range(
                    min(pattern_length, len(candidate)), -1, -1
                ):
                    if candidate.endswith(pattern[:length]):
                        next_state = length
                        break

            # Save the next state for this symbol.
            transitions[state][symbol] = next_state

    return transitions


def display_transition_table(pattern, transitions):
    print("\nDFA TRANSITION TABLE")
    print("-" * 35)
    print(f"{'State':<12}{'Input 0':<12}{'Input 1':<12}")
    print("-" * 35)

    # Display each state's destination for 0 and 1.
    for state in range(len(pattern) + 1):
        state_name = f"q{state}"

        # Mark the final state as the accepting state.
        if state == len(pattern):
            state_name += " (Accept)"

        print(
            f"{state_name:<12}"
            f"q{transitions[state]['0']:<11}"
            f"q{transitions[state]['1']:<11}"
        )

    print("-" * 35)


def simulate_dfa(input_string, pattern, transitions):
    # The DFA always starts at q0.
    current_state = 0

    print("\nSIMULATION")
    print("-" * 40)
    print("Input string:", input_string)
    print("Target pattern:", pattern)
    print("Starting state: q0")
    print("\nState transitions:")

    # Read each input character and follow the transition table.
    for symbol in input_string:
        next_state = transitions[current_state][symbol]

        print(
            f"q{current_state} -- {symbol} --> q{next_state}"
        )

        # Move to the next state.
        current_state = next_state

    # Accept if the final state equals the pattern length.
    print("\nFinal state: q" + str(current_state))

    if current_state == len(pattern):
        print("Result: ACCEPTED")
        print(f"The string contains the pattern '{pattern}'.")
    else:
        print("Result: REJECTED")
        print(f"The string does not contain the pattern '{pattern}'.")

    print("-" * 40)


def main():
    print("=" * 45)
    print("DFA PATTERN DETECTION SIMULATOR")
    print("Alphabet: 0 and 1")
    print("=" * 45)

    # User inputs a pattern that they want
    while True:
        pattern = input("\nEnter the binary pattern to search for (or 'exit'): ").strip()

        # Exit the program when exit is typed
        if pattern.lower() == "exit":
            print("DFA Simulator closed.")
            break

        # Patterns must be non-empty and contain only 0 and 1.
        if not pattern or any(char not in "01" for char in pattern):
            print("Invalid pattern. Enter only 0 and 1.")
            continue

        # Build and display the DFA for the selected pattern.
        transitions = build_dfa(pattern)
        display_transition_table(pattern, transitions)

        # Allow the user to test multiple strings with this DFA.
        while True:
            input_string = input("\nEnter a binary string ('pattern' to change pattern, 'exit' to quit): ").strip()

            if input_string.lower() == "exit":
                print("DFA Simulator closed.")
                return

            # Return to pattern selection.
            if input_string.lower() == "pattern":
                break

            # Input strings must contain only 0 and 1.
            if not input_string or any(char not in "01" for char in input_string):
                print("Invalid string. Enter only 0 and 1.")
                continue

            # Run the simulation using the generated DFA.
            simulate_dfa(input_string, pattern, transitions)


if __name__ == "__main__":
    main()
