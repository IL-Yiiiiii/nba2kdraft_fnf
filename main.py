# =========================================================
# 🚀 GLOBAL LIVE PICK & TURN NOTIFICATION SYSTEM
# =========================================================
if shared_draft.get("draft_mode") and shared_draft.get("headliners_resolved"):
    history = shared_draft.get("draft_history", [])
    current_pick_idx = len(history)
    total_teams, total_rounds = 7, 8

    # 🛑 1. TEMPORARY "JUST DRAFTED" POP-UP (Fires exactly once per new pick)
    # Initialize the user's personal pick tracker if it doesn't exist yet
    if "last_seen_pick_idx" not in st.session_state:
        st.session_state["last_seen_pick_idx"] = current_pick_idx

    # If the global history has grown, a new pick happened!
    if current_pick_idx > st.session_state["last_seen_pick_idx"]:
        prev_idx = current_pick_idx - 1
        prev_r = (prev_idx // total_teams) + 1
        prev_p = (prev_idx % total_teams) + 1
        
        if prev_r % 2 != 0:
            prev_owner = shared_draft["draft_order"][prev_p - 1]
        else:
            prev_owner = shared_draft["draft_order"][total_teams - prev_p]
            
        # Fire the temporary alert
        st.toast(f"🏃‍♂️ {prev_owner.capitalize()} just drafted {history[-1]}!", icon="🔥")
        
        # Mark this pick as "seen" so it disappears on the next click/refresh
        st.session_state["last_seen_pick_idx"] = current_pick_idx


    # ⏰ 2. "YOU ARE ON THE CLOCK" POP-UP (Fires on every refresh while it's their turn)
    if current_pick_idx < (total_teams * total_rounds):
        curr_r = (current_pick_idx // total_teams) + 1
        curr_p = (current_pick_idx % total_teams) + 1
        
        if curr_r % 2 != 0:
            current_owner = shared_draft["draft_order"][curr_p - 1]
        else:
            current_owner = shared_draft["draft_order"][total_teams - curr_p]

        if username == current_owner:
            st.toast(f"🚨 YOU ARE ON THE CLOCK! (Round {curr_r}.{curr_p})", icon="⏰")
