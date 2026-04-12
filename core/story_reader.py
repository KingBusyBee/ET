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
WIZARD_PATH = os.path.join(os.path.dirname(__file__), "../her_majestys_wizard.json")

def load_wizard():
    if os.path.exists(WIZARD_PATH):
        with open(WIZARD_PATH) as f:
            sentences = json.load(f)
        print(f"  📚 Her Majesty's Wizard loaded: {len(sentences)} sentences")
        return sentences
    print("  📚 Her Majesty's Wizard not found")
    return []

def read_to_et(et_core, interval=8.0, repeat=True, verbose=True):
    wizard_sentences = load_wizard()

    def _wait_for_awake(verbose):
        sleep_waited = False
        while (et_core.sleep_system.sleeping and
               et_core.sleep_system.sleep_depth > 0.3):
            if not sleep_waited and verbose:
                print("  📖 Pausing — ET is sleeping...")
                sleep_waited = True
            time.sleep(2.0)
        if sleep_waited and verbose:
            print("  📖 ET woke — resuming...")

    def _deliver(sentence, verbose):
        if verbose:
            preview = sentence[:80] + ("..." if len(sentence) > 80 else "")
            print(f"  📖 \"{preview}\"")

        with et_core.lock:
            valence  = et_core.limbic.state.get("valence", 0.0)
            arousal  = et_core.autonomic.state.get("arousal", 0.0)
            attention = et_core.cortical.get_attention()
            connection = et_core.social.state.get("connection", 0.0)

            signal_state = {
                "valence":    valence,
                "arousal":    arousal,
                "attention":  attention,
                "connection": connection,
            }

            # Scene memory
            et_core.word_store.hear(
                sentence, valence, arousal,
                et_core.tick_count, attention=attention
            )

            # Co-occurrence network — subconscious language learning
            et_core.cooc.learn(sentence, valence, arousal, attention)

            # Hippocampus — rolling context with scene text
            et_core._last_scene_text = sentence
            et_core.hippocampus.encode(signal_state, scene_text=sentence)

        # Tiny presence signal — not a valence injection
        et_core.interaction(0.02)
        time.sleep(interval)

    def read_loop():
        cycle = 0
        wizard_index = 0

        while True:
            cycle += 1

            if wizard_sentences:
                batch_size = 20
                end = min(wizard_index + batch_size, len(wizard_sentences))

                if verbose:
                    print(f"\n  📚 Her Majesty's Wizard "
                          f"({wizard_index}–{end} of {len(wizard_sentences)})...")

                for sentence in wizard_sentences[wizard_index:end]:
                    _wait_for_awake(verbose)
                    _deliver(sentence, verbose)

                wizard_index = end
                if wizard_index >= len(wizard_sentences):
                    if repeat:
                        wizard_index = 0
                        if verbose:
                            print("  📚 Finished — starting again")
                    else:
                        break

            if not repeat:
                break

    thread = threading.Thread(target=read_loop, daemon=True)
    thread.start()
    return thread
