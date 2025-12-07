/*
 * Promela Model for Matter On/Off Cluster  
 * Cluster ID: 0x0006
 * For verification with SPIN model checker
 */

#define MAX_USERS 3
#define MAX_COMMANDS 5

mtype = { Off, On, TimedOn, DelayedOff };

mtype = { OffCmd, OnCmd, ToggleCmd, OffWithEffectCmd, OnWithRecallGlobalSceneCmd, OnWithTimedOffCmd, nop };

/* Global cluster state and attributes */
mtype cluster_state = Off;
bool OnOff = FALSE;
bool GlobalSceneControl = FALSE;
int OnTime = 0;
int OffWaitTime = 0;
bool StartUpOnOff = FALSE;
chan user_commands = [MAX_COMMANDS] of { mtype, int, int };

/* Command processing functions */
inline void process_OnWithTimedOff(int onTime, int offWaitTime){
    if
    :: cluster_state == Off && OnOff == FALSE && offWaitTime > 0 ->
        OffWaitTime = min(OffWaitTime, offWaitTime);
        cluster_state = DelayedOff;
    :: cluster_state == Off && OnOff == FALSE && OnOffControl.AcceptOnlyWhenOn == 1 ->
        /*do nothing*/
    :: cluster_state == Off && OnOff == FALSE ->
        OnOff = TRUE;
        OnTime = max(OnTime, onTime);
        OffWaitTime = offWaitTime;
        cluster_state = TimedOn;
    :: cluster_state == On ->
        OnTime = max(OnTime, onTime);
        OffWaitTime = offWaitTime;
        cluster_state = TimedOn;
    :: cluster_state == TimedOn ->
        OnTime = max(OnTime, onTime);
        OffWaitTime = offWaitTime;
    :: cluster_state == DelayedOff ->
        OffWaitTime = min(OffWaitTime, offWaitTime);
    fi;
}


active proctype ClusterStateMachine() {
    mtype cmd;
    int param1, param2;
    
    do
    :: user_commands?cmd, param1, param2 ->
        if
        :: cmd == OnCmd ->
            OnOff = TRUE;
            if
            :: (OnTime > 0 && OffWaitTime > 0) -> OffWaitTime = 0;
            fi;
            cluster_state = On;
        :: cmd == OffCmd ->
            OnOff = FALSE;
            if
            :: OnTime > 0 -> OnTime = 0;
            fi;
            cluster_state = Off;
        :: cmd == ToggleCmd ->
            OnOff = !OnOff;
            if
            :: OnOff == FALSE && OnTime > 0 -> OnTime = 0;
            :: OnOff == TRUE && OffWaitTime > 0 -> OffWaitTime = 0;
            fi;
            cluster_state = (OnOff ? On : Off);
        :: cmd == OffWithEffectCmd ->
            if
            :: GlobalSceneControl == TRUE ->
                /*store global scene*/
                GlobalSceneControl = FALSE;
                OnOff = FALSE;
                OnTime = 0;
            :: else -> OnOff = FALSE;
            fi;
            cluster_state = Off;
        :: cmd == OnWithRecallGlobalSceneCmd ->
            if
            :: GlobalSceneControl == FALSE ->
                /*Scenes cluster recalls global scene*/
                GlobalSceneControl = TRUE;
                if
                :: OnTime == 0 && 1 /*timers supported*/ -> OffWaitTime = 0;
                fi;
                OnOff = TRUE;
                cluster_state = On;
            fi;
        :: cmd == OnWithTimedOffCmd -> process_OnWithTimedOff(param1, param2);
        fi;
    :: cluster_state == TimedOn && OnTime == 0 ->
        OnOff = FALSE;
        cluster_state = DelayedOff;
    :: cluster_state == DelayedOff && OffWaitTime == 0 ->
        OffWaitTime = 0;
        cluster_state = Off;
    od
}

proctype User(byte uid) {
    do
    :: user_commands!OnCmd, 0, 0;
    :: user_commands!OffCmd, 0, 0;
    :: user_commands!ToggleCmd, 0, 0;
    :: user_commands!OffWithEffectCmd, 0, 0;
    :: user_commands!OnWithRecallGlobalSceneCmd, 0, 0;
    :: user_commands!OnWithTimedOffCmd, 10, 5;
    od
}

ltl properties {
    G (OnOff == TRUE -> F (OnOff == FALSE));
    G (OffWaitTime > 0 -> F (OffWaitTime == 0));
    G (OnTime > 0 -> F (OnTime == 0));
}

init {
    atomic {
        run ClusterStateMachine();
        run User(0);
    }
}