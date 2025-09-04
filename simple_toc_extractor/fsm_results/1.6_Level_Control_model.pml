/*
 * Promela Model for Level Control Cluster
 * Cluster ID: 0x0008
 * For verification with SPIN model checker
 */

#define MAX_LEVEL 100
#define MIN_LEVEL 0

mtype = { Idle, MovingToLevel, Moving, Stepping };

mtype = { MoveToLevel, Move, Step, Stop, MoveToLevelWithOnOff, MoveWithOnOff, StepWithOnOff, StopWithOnOff };

mtype cluster_state = Idle;
int CurrentLevel = 0;
int RemainingTime = 0;
int MinLevel = 0;
int MaxLevel = MAX_LEVEL;
int TransitionTime = 0;
int Rate = 0;
int StepSize = 0;
int TargetLevel = 0;
chan user_commands = [10] of { mtype, int, int, int };


inline process_MoveToLevel(targetLevel, transitionTime) {
    if
    :: (targetLevel >= MinLevel && targetLevel <= MaxLevel) ->
        atomic {
            cluster_state = MovingToLevel;
            TargetLevel = targetLevel;
            RemainingTime = transitionTime;
        }
    fi
}

inline process_Move(direction, rate) {
    atomic {
        cluster_state = Moving;
        Rate = rate;
        RemainingTime = abs(TargetLevel - CurrentLevel) / Rate; //Simplified time calculation
    }
}

inline process_Step(direction, stepSize) {
    atomic {
        cluster_state = Stepping;
        StepSize = stepSize;
        RemainingTime = 1; //Simplified time calculation
    }
}

inline process_Stop() {
    atomic {
        cluster_state = Idle;
        RemainingTime = 0;
        Rate = 0;
        StepSize = 0;
    }
}


active proctype ClusterStateMachine() {
    mtype cmd;
    int param1, param2, param3;
    do
    :: user_commands?cmd, param1, param2, param3 ->
        if
        :: (cmd == MoveToLevel || cmd == MoveToLevelWithOnOff) ->
            process_MoveToLevel(param1, param2);
        :: (cmd == Move || cmd == MoveWithOnOff) ->
            process_Move(param1, param2);
        :: (cmd == Step || cmd == StepWithOnOff) ->
            process_Step(param1, param2);
        :: (cmd == Stop || cmd == StopWithOnOff) ->
            process_Stop();
        fi
    :: (cluster_state == MovingToLevel && RemainingTime > 0) ->
        RemainingTime--;
        if
        :: (RemainingTime == 0) ->
            CurrentLevel = TargetLevel;
            cluster_state = Idle;
        fi
    :: (cluster_state == Moving && RemainingTime > 0) ->
        RemainingTime--;
        CurrentLevel = CurrentLevel + (Rate > 0 ? 1 : -1);
        if
        :: (RemainingTime == 0) ->
            cluster_state = Idle;
        fi
    :: (cluster_state == Stepping && RemainingTime > 0) ->
        RemainingTime--;
        CurrentLevel = CurrentLevel + StepSize;
        cluster_state = Idle;
    od
}

proctype User() {
    do
    :: user_commands!MoveToLevel, 50, 10, 0;
    :: user_commands!Move, 1, 5;
    :: user_commands!Step, 1, 10;
    :: user_commands!Stop, 0, 0, 0;
    od
}

ltl safety1 { [](CurrentLevel >= MinLevel && CurrentLevel <= MaxLevel) }
ltl safety2 { [](RemainingTime >= 0) }
ltl liveness1 { []<>(cluster_state == Idle) }


init {
    atomic {
        run ClusterStateMachine();
        run User();
    }
}