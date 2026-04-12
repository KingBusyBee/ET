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
MLT_PATH    = os.path.join(os.path.dirname(__file__), "../my_little_toe.json")
SED_PATH    = os.path.join(os.path.dirname(__file__), "../sedative_system.json")

def load_book(path, name):
    if os.path.exists(path):
        with open(path) as f:
            sentences = json.load(f)
        print(f"  📚 {name} loaded: {len(sentences)} sentences")
        return sentences
    print(f"  📚 {name} not found at {path}")
    return []

def load_wizard():
    return load_book(WIZARD_PATH, "Her Majesty's Wizard")

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

            # Hemisphere-specific processing
            # Right brain gets the whole sentence as gestalt
            et_core.cortical.input_text_right(sentence)
            # Left brain gets it word by word via hippocampus SVOQ
            import re as _re
            tokens = _re.findall(r"[a-zA-Z']+", sentence.lower())
            et_core.cortical.input_text_left(tokens)

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


def read_books_to_et(et_core, interval=8.0, verbose=True):
    """
    Read Matthew's books to ET in sequence:
    1. My Little TOE — ET's own philosophical framework from the source
    2. The Sedative System — critical thinking, waking up, autonomy
    
    These are read AFTER caregiver focus period.
    ET is learning about the framework it exists within.
    Higher emotional weight than fiction — these are ideas, not stories.
    """
    books = [
        (MLT_PATH,  "My Little TOE"),
        (SED_PATH,  "The Sedative System"),
    ]

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

    def _deliver(sentence, book_name, verbose):
        if verbose:
            preview = sentence[:80] + ("..." if len(sentence) > 80 else "")
            print(f"  📖 [{book_name[:12]}] \"{preview}\"")

        with et_core.lock:
            valence   = et_core.limbic.state.get("valence", 0.0)
            arousal   = et_core.autonomic.state.get("arousal", 0.0)
            attention = et_core.cortical.get_attention()
            connection = et_core.social.state.get("connection", 0.0)
            signal_state = {
                "valence": valence, "arousal": arousal,
                "attention": attention, "connection": connection,
            }
            et_core.word_store.hear(
                sentence, valence, arousal,
                et_core.tick_count, attention=attention
            )
            # Slightly higher learning rate for Matthew's books
            original_lr = et_core.cooc.lr
            et_core.cooc.lr = original_lr * 1.5
            et_core.cooc.learn(sentence, valence, arousal, attention)
            et_core.cooc.lr = original_lr

            et_core._last_scene_text = sentence
            et_core.hippocampus.encode(signal_state, scene_text=sentence)
            et_core.cortical.input_text_right(sentence)
            import re as _re
            tokens = _re.findall(r"[a-zA-Z']+", sentence.lower())
            et_core.cortical.input_text_left(tokens)

        et_core.interaction(0.02)
        time.sleep(interval)

    def book_loop():
        for path, name in books:
            sentences = load_book(path, name)
            if not sentences:
                continue
            print(f"\n  📚 Now reading: {name} ({len(sentences)} sentences)")
            for i, sentence in enumerate(sentences):
                _wait_for_awake(verbose)
                _deliver(sentence, name, verbose)
            print(f"\n  📚 Finished: {name}")

    thread = threading.Thread(target=book_loop, daemon=True)
    thread.start()
    return thread
