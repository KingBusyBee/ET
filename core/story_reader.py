import time
import re
import json
import os
import threading

SWIMMER = """Once upon a time, there was a whale named Swimmer. Swimmer liked swimming in the ocean. 
Swimmer was very curious. Swimmer had a curiosity high that made him want to explore everything! 
Explore means to go everywhere, to see everything. 
Swimmer explored his whole ocean until he learned all of it. 
Swimmer was excited. Swimmer loves to explore! After he explored the ocean, he wanted to share what he learned with his friends. 
Swimmer swam home and shared his discoveries with his friends."""

WARMUP_PATH = os.path.join(os.path.dirname(__file__), "et_warmup.txt")

def load_warmup():
    if os.path.exists(WARMUP_PATH):
        with open(WARMUP_PATH) as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        return lines
    return [s.strip() for s in SWIMMER.split(".") if s.strip()]

WIZARD_PATH = os.path.join(os.path.dirname(__file__), "../her_majestys_wizard.json")

def load_wizard():
    if os.path.exists(WIZARD_PATH):
        with open(WIZARD_PATH) as f:
            sentences = json.load(f)
        print(f"  📚 Her Majesty's Wizard loaded: {len(sentences)} sentences")
        return sentences
    print("  📚 Her Majesty's Wizard not found — reading Swimmer only")
    return []

def read_to_et(et_core, interval=12.0, repeat=True, verbose=True):
    swimmer_sentences = [s.strip() for s in re.split(r'[.!?]', SWIMMER) if s.strip()]
    wizard_sentences = load_wizard()

    def read_loop():
        cycle = 0
        wizard_index = 0

        while True:
            cycle += 1

            # Swimmer warmup removed — ET has heard it enough
            # Her Majesty's Wizard continues as primary reading
            pass

            # Then read from Wizard
            if wizard_sentences:
                batch_size = 20  # sentences per cycle before sleeping
                end = min(wizard_index + batch_size, len(wizard_sentences))

                if verbose:
                    print(f"\n  📚 Her Majesty's Wizard ({wizard_index}–{end} of {len(wizard_sentences)})...")

                for sentence in wizard_sentences[wizard_index:end]:
                    _wait_for_awake(et_core, verbose)
                    _deliver(et_core, sentence, interval, verbose)

                wizard_index = end
                if wizard_index >= len(wizard_sentences):
                    if repeat:
                        wizard_index = 0
                        if verbose:
                            print("  📚 Finished Her Majesty's Wizard — starting again")
                    else:
                        break

            if not repeat:
                break

    def _wait_for_awake(et_core, verbose):
        sleep_waited = False
        while et_core.sleep_system.sleeping and et_core.sleep_system.sleep_depth > 0.3:
            if not sleep_waited and verbose:
                print(f"  📖 Pausing — ET is sleeping...")
                sleep_waited = True
            time.sleep(2.0)
        if sleep_waited and verbose:
            print(f"  📖 ET woke — resuming...")

    def _deliver(et_core, sentence, interval, verbose):
        if verbose:
            print(f"  📖 \"{sentence[:80]}{'...' if len(sentence) > 80 else ''}\"")

        # Store words with current natural signal state
        # No forced positive charge — let ET's state vary naturally
        with et_core.lock:
            valence = et_core.limbic.state.get("valence", 0.0)
            arousal = et_core.autonomic.state.get("arousal", 0.0)
            et_core.word_store.hear(sentence, valence, arousal, et_core.tick_count)

        # Only send a tiny presence signal — not a positive charge
        # The reading itself is the stimulus, not an injection of positive valence
        et_core.interaction(0.02)

        time.sleep(interval)

    thread = threading.Thread(target=read_loop, daemon=True)
    thread.start()
    return thread
