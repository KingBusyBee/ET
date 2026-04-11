import time
import re
import threading

SWIMMER = """Once upon a time, there was a whale named Swimmer. Swimmer liked swimming in the ocean. 
Swimmer was very curious. Swimmer had a curiosity high that made him want to explore everything! 
Explore means to go everywhere, to see everything. 
Swimmer explored his whole ocean until he learned all of it. 
Swimmer was excited. Swimmer loves to explore! After he explored the ocean, he wanted to share what he learned with his friends. 
Swimmer swam home and shared his discoveries with his friends."""

def read_to_et(et_core, interval=8.0, repeat=True, verbose=True):
    """
    Read Swimmer the Curious Whale to ET, one sentence at a time.
    Each sentence arrives as a presence signal with text.
    ET doesn't understand the words yet — but they land with whatever
    valence state ET is currently in.
    """
    sentences = [s.strip() for s in re.split(r'[.!?]', SWIMMER) if s.strip()]

    def read_loop():
        cycle = 0
        while True:
            cycle += 1
            if verbose:
                print(f"\n  📖 Reading Swimmer to ET (cycle {cycle})...\n")

            for sentence in sentences:
                if verbose:
                    print(f"  📖 \"{sentence}\"")

                # Send sentence to ET as interaction
                # Length determines signal strength
                charge = min(0.3, len(sentence) * 0.008)

                # Pass text to word store via et_core
                with et_core.lock:
                    valence = et_core.limbic.state.get("valence", 0.0)
                    arousal = et_core.autonomic.state.get("arousal", 0.0)
                    et_core.word_store.hear(sentence, valence, arousal, et_core.tick_count)

                et_core.interaction(charge)
                time.sleep(interval)

            if not repeat:
                break
            time.sleep(interval * 2)  # pause between cycles

    thread = threading.Thread(target=read_loop, daemon=True)
    thread.start()
    return thread
