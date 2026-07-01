elif option == "Headliner Players":
    st.title("***HEADLINERS***")
    st.subheader("***NOTE:***")
    st.write("**The draft is in serpentine order - so in even rounds the 7th pick will go 1st, 6th go 2nd, and so on.**")
    st.write("**Example:** Round 1: 1,2,3,4,5,6,7 | Round 2: 7,6,5,4,3,2,1")
    st.write("*> Picking a 99 will get you a pick in the range* **4-7**.")
    st.write("*> Picking a 98 will get you a pick in the range* **1-3**.")
    st.write("> **CONTEST SYSTEM:** If multiple people pick a player the person who gets the player is decided by random and the person (or people) who did not get the player has to pick from the remaining headliners.")
    st.write("Also: The efficiencies are more normal in the playoffs, for example, 3PT shooting % for mid shooters falls to mid 30 percentages")
    st.header("*:green[UNDRAFTED]*")
    display_t1()
    st.header("*:red[DRAFTED]*")
    if shared_draft["drafted_t1_array"]:
        for i in range(len(shared_draft["drafted_t1_array"])):
            display_player(shared_draft["drafted_t1_array"][i])

elif option == "Search Players":
    st.title("*PLAYER SEARCH*")
    st.subheader("About the players:")
    st.write("Players in sets 2020-2026 have their ratings based on their projected primes.")
    st.write("Note: The efficiencies are more normal in the playoffs, for example, 3PT shooting % for mid shooters falls to mid 30 percentages")
    st.write("Also: Players who took a low volume of 3s (that shouldn't have) due to system profiency get put at 0 3P%")
    col_pos, col_attribute = st.columns([6,8])
    with col_pos:
        playstyle_select = st.selectbox("Playstyle Filter:",
                     ["None", "3-Level Scorer", "Sharpshooter", "Mid Range Assassin", "Crafty Finisher", "Explosive Finisher",
                      "Paint Beast", "Stretch Big", "Defensive Anchor", "Perimeter Lockdown",
                      "Versatile Defender", "Two Way", "Floor General",
                      "Playmaking Maestro", "Swiss Army Knife"], key="ps_choice")
        pos_filter = st.segmented_control("Position Filter:", ["PG", "SG", "SF", "PF", "C"], key="pos_choice")
        sec_allowed = st.toggle("Allow secondary position", key="sec_choice")
        st.button("***:yellow[RESET FILTERS]***", on_click=reset)
    with col_attribute:
        attribute_select = st.selectbox("Attribute Filter:", ["None","Inside Scoring", "Mid-Range Shooting", "3-Point Shooting", "Playmaking", "Interior Defense", "Perimeter Defense", "Rebounding", "Athleticism"], key="a_choice")
        max_grade_select = st.select_slider("Max Attribute Grade:",["S", "A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"], key="max_a_choice")
        min_grade_select = st.select_slider("Min Attribute Grade:",["F", "D-", "D", "D+", "C-", "C", "C+", "B-", "B", "B+", "A-", "A", "A+", "S"], key="min_a_choice")
    st.markdown("---")
    st.header("*:green[UNDRAFTED]*")
    for i in range(len(shared_draft["player_array"])):
        if check_playstyles(shared_draft["player_array"][i], playstyle_select) and check_attribute(
                shared_draft["player_array"][i], attribute_select, min_grade_select, max_grade_select,
                make_attribute_dict()) and check_position(shared_draft["player_array"][i], pos_filter, sec_allowed):
            display_player(shared_draft["player_array"][i])
    st.markdown("---")
    st.header("*:red[DRAFTED]*")
    if shared_draft["drafted_player_array"]:
        for i in range(len(shared_draft["drafted_player_array"])):
            display_player(shared_draft["drafted_player_array"][i])

elif option == "Compare Players":
    st.title("*COMPARE PLAYERS*")
    st.subheader("*Click on a player in 'Search Players' or 'Headliner Players' and click compare player to add here:*")
    if st.button(":yellow[Reset compare]", key="reset_compare"):
        st.session_state.compare_array = []
        st.rerun()
    st.markdown("""
        <style>
            div[data-testid="column"] {
                padding: 0px;
            }
            div[data-testid="stButton"] button {
                width: 100%;
            }
        </style>
    """, unsafe_allow_html=True)
    if st.session_state.compare_array:
        player_names = [p.name for p in st.session_state.compare_array]
        #col_remove_select, col_remove_button = st.columns([6,6], vertical_alignment="bottom")
        #with col_remove_select:
            #player_remove = st.selectbox("Remove player:", player_names)
        #with col_remove_button:
            #if st.button(":red[Remove]"):
                #st.session_state.compare_array = [p for p in st.session_state.compare_array if p.name != player_remove]
                #st.rerun()

        n = len(st.session_state.compare_array)

        # Match the ratio to your df's row-label vs data columns
        col_widths = [1.5] + [1] * n
        cols = st.columns(col_widths)

        with cols[0]:
            st.write("")  # empty space for row label column

        for i, player in enumerate(st.session_state.compare_array):
            with cols[i + 1]:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.compare_array.pop(i)
                    st.rerun()

    load_to_df(st.session_state.compare_array)
    st.dataframe(st.session_state.compare_df.T, width='stretch')

elif option == "Draft Room":
    st.title("*DRAFT ROOM*")

    if not shared_draft["draft_mode"]:
        st.warning("🚨 The draft has not started yet! Waiting on the admin to initiate...")

    else:
        username = st.session_state.get("username", "Guest")

        # --- PHASE 1 DISPLAY: WAITING ON BLIND HEADLINERS ---
        if not shared_draft["headliners_resolved"]:
            st.subheader("🎯 Phase 1: Headliner Submission Status")

            if username in shared_draft.get("coin_flip_losers", []):
                st.error(
                    "❌ YOU LOST THE RANDOMIZER! Your choice was taken. Head back to the Headliners tab and pick a remaining player!")
            elif username in shared_draft.get("headheadline_picks", {}):
                st.success(
                    f"✅ You have securely submitted your choice: **{shared_draft['headliner_picks'][username]}**")
            else:
                st.info("👋 Go to the **Headliners** tab and click 'Draft Player' on your top choice to begin!")

            st.divider()

            # Show who has checked in
            picks_count = len(shared_draft.get('headliner_picks', {}))
            st.markdown(f"**Submissions received:** `{picks_count} / 7`")

            for user, pick in shared_draft.get("headliner_picks", {}).items():
                # Admin sees what they picked, normal users just see that they submitted
                if st.session_state.get("name") == "Isaac":
                    st.write(f"- **{user.capitalize()}** selected *{pick}*")
                else:
                    st.write(f"- **{user.capitalize()}** has locked in a choice.")

            # Admin Button to run coin flips and sort 98/99s
            # MOVED: Placed cleanly outside the 'for' loop so it can render for Isaac
            if username.lower() == "isaac" and picks_count == 7:
                st.write("")
                if st.button("Resolve Contests & Generate Draft Order", type="primary"):

                    pick_counts = {}
                    for u, p_name in shared_draft["headliner_picks"].items():
                        if p_name not in pick_counts:
                            pick_counts[p_name] = []
                        pick_counts[p_name].append(u)

                    losers_this_round = []

                    for p_name, users in pick_counts.items():
                        winner = random.choice(users)
                        player_obj = next((p for p in shared_draft["t1_array"] if p.name == p_name), None)

                        if player_obj:
                            if winner not in shared_draft["all_teams"]:
                                shared_draft["all_teams"][winner] = []
                            shared_draft["all_teams"][winner].append(player_obj.clone())
                            shared_draft["drafted_t1_array"].append(player_obj.clone())
                            shared_draft["t1_array"] = [p for p in shared_draft["t1_array"] if p.name != p_name]

                        for u in users:
                            if u != winner:
                                losers_this_round.append(u)
                                del shared_draft["headliner_picks"][u]

                    if len(losers_this_round) > 0:
                        shared_draft["coin_flip_losers"] = losers_this_round
                    else:
                        # Clean finish! Separate and shuffle 98s vs 99s
                        shared_draft["headliners_resolved"] = True
                        pool_98 = []
                        pool_99 = []
                        pool_other = []

                        for u in shared_draft["headliner_picks"].keys():
                            roster = shared_draft["all_teams"].get(u, [])
                            if roster:
                                try:
                                    rating = int(roster[0].rating)
                                    if rating == 98:
                                        pool_98.append(u)
                                    elif rating == 99:
                                        pool_99.append(u)
                                    else:
                                        pool_other.append(u)
                                except ValueError:
                                    pool_other.append(u)
                            else:
                                pool_other.append(u)

                        random.shuffle(pool_98)
                        random.shuffle(pool_99)
                        random.shuffle(pool_other)

                        shared_draft["draft_order"] = pool_98 + pool_99 + pool_other

                        save_draft_state(shared_draft)

                    st.rerun()

        # --- PHASE 2 DISPLAY: THE LIVE PROGRESS TIMELINE ---
        # MOVED: Properly aligned with Phase 1 out of the loop
        elif shared_draft["headliners_resolved"]:
            # Dynamic Pick Position and Current Pick
            if shared_draft["headliners_resolved"]:
                # 1. Find their pick position
                if username in shared_draft["draft_order"]:
                    pick_pos = shared_draft["draft_order"].index(username) + 1
                    st.subheader(f"Your pick position: **{pick_pos}**")
                else:
                    st.subheader(f"Your pick position: **N/A**")

                # 2. Calculate the current round and pick on the clock
                current_pick_idx = len(shared_draft.get("draft_history", []))
                curr_r = (current_pick_idx // 7) + 1
                curr_p = (current_pick_idx % 7) + 1
                st.subheader(f"Current Round/Pick: **{curr_r}.{curr_p}**")
            else:
                # Fallback text while Headliners are still being picked
                st.subheader("Your pick position: **TBD (Pending Headliners)**")
                st.subheader("Current Round/Pick: **Phase 1**")

            st.button("Trade pick position")

            # Dynamic Team Overview
            st.subheader("Your team: ")
            user_roster = shared_draft["all_teams"].get(username, [])
            if user_roster:
                st.write(f"You currently have **{len(user_roster)}** player(s) drafted.")
            else:
                st.write("No players drafted yet.")

            st.button("Go to team")
            history = shared_draft.get("draft_history", [])
            current_pick_idx = len(history)

            total_teams = 7
            total_rounds = 8

            curr_r = (current_pick_idx // total_teams) + 1
            curr_p = (current_pick_idx % total_teams) + 1

            # 📢 NEW: GLOBAL RECENT PICK ANNOUNCEMENT
            if len(history) > 0:
                prev_idx = current_pick_idx - 1
                prev_r = (prev_idx // total_teams) + 1
                prev_p = (prev_idx % total_teams) + 1
                if prev_r % 2 != 0:
                    prev_owner = shared_draft["draft_order"][prev_p - 1]
                else:
                    prev_owner = shared_draft["draft_order"][total_teams - prev_p]

                st.success(f"📢 **LATEST DRAFT PICK:** **{prev_owner.capitalize()}** selected **{history[-1]}**!")

            st.write("")

            if current_pick_idx < (total_teams * total_rounds):
                if curr_r % 2 != 0:
                    current_owner = shared_draft["draft_order"][curr_p - 1]
                else:
                    current_owner = shared_draft["draft_order"][total_teams - curr_p]

                st.info(f"⚡ **ON THE CLOCK:** Round {curr_r}.{curr_p} — **{current_owner.capitalize()}**")
                if username == current_owner:
                        # Trigger the pop-up notification
                    st.error("👉 IT IS YOUR TURN! Head to 'Search Players' to draft a player.")
            else:
                st.balloons()
                st.success("🎉 The draft is officially complete!")

            st.write("")
            with st.expander("👑 View Phase 1: Headliner Selections", expanded=False):
                for team_owner, roster in shared_draft["all_teams"].items():
                    if roster:
                        st.write(
                            f"- **{team_owner.capitalize()}** secured: *{roster[0].name} ({roster[0].rating} OVR)*")

            st.divider()
            st.subheader("📋 Draft Progress Board")

            for pick_num in range(total_rounds * total_teams):
                r = (pick_num // total_teams) + 1
                p = (pick_num % total_teams) + 1

                if r % 2 != 0:
                    owner = shared_draft["draft_order"][p - 1]
                else:
                    owner = shared_draft["draft_order"][total_teams - p]

                if pick_num < len(history):
                    st.write(f"🟢 **Round {r}.{p}** | **{owner.capitalize()}** ➔ *{history[pick_num]}*")
                elif pick_num == len(history):
                    st.markdown(f"🟠 **Round {r}.{p}** | **{owner.capitalize()}** ➔ `🤔 NOW PICKING...`")
                else:
                    st.write(f"⚪ Round {r}.{p} | {owner.capitalize()} ➔ ⏳ *Pending*")

elif option == "Teams":
    st.title("*TEAMS*")
    st.subheader("*YOUR TEAM:*")

    username = st.session_state.get("username", "Guest")
    user_team = shared_draft["all_teams"].get(username, [])

    if user_team:
        st.write(f"Player Count: {len(user_team)}")
        for i in range(len(user_team)):
            display_player(user_team[i])
    else:
        st.write("You haven't drafted any players yet!")

    if not shared_draft["draft_mode"]:
        st.divider()
        st.subheader("*THIS PAGE WILL CHANGE IN DRAFT MODE!*")

    if shared_draft["draft_mode"]:
        st.divider()
        st.subheader("*OTHER TEAMS:*")

        other_teams = {owner: roster for owner, roster in shared_draft["all_teams"].items() if owner != username}

        if not other_teams:
            st.write("No one else has drafted any players yet!")
        else:
            for team_owner, roster in other_teams.items():
                with st.expander(f"{team_owner.capitalize()}'s Team ({len(roster)} players)"):
                    if not roster:
                        st.write(f"*{team_owner.capitalize()} hasn't drafted anyone yet.*")
                    else:
                        for player in roster:
                            display_player(player)

elif option == "Trade Hub":
    st.title("*TRADE HUB*")
    if not shared_draft["draft_mode"]:
        st.subheader("**Will open in draft mode!**")

elif option == "Results":
    st.title("*RESULTS*")
    st.subheader("**< YEAR 1 >**")
    st.write("*WAITING!*")
    st.subheader("**< YEAR 2 >**")
    st.write("*WAITING!*")
    st.subheader("**< YEAR 3 >**")
    st.write("*WAITING!*")
    st.subheader("**< YEAR 4 >**")
    st.write("*WAITING!*")
    st.subheader("**< YEAR 5 >**")
    st.write("*WAITING!*")
    st.subheader("**< YEAR 6 >**")
    st.write("*WAITING!*")
    st.subheader("**< YEAR 7 >**")
    st.write("*WAITING!*")
