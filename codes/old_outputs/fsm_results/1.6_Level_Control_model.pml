/*
 * Promela Model for Matter Level Control Cluster  
 * Cluster ID: 0x0008
 * For verification with SPIN model checker
 */

#define MAX_USERS 3
#define MAX_COMMANDS 5

/* State enumeration from FSM states */
mtype state = {Idle, MovingToLevel, Moving, Stepping, Stopped, MovingToFrequency};

/* Command types from FSM commands_handled */
mtype command = {MoveToLevel, Move, Step, Stop, MoveToClosestFrequency, nop};

/* Global cluster state and attributes */
mtype cluster_state = Idle;
int CurrentLevel = 0;
int RemainingTime = 0;
int MinLevel = 0;
int MaxLevel = 100;
int Rate = 0;
int StepSize = 0;
int CurrentFrequency = 0;
int Level = 0;
int TransitionTime = 0;
chan user_commands = [MAX_COMMANDS] of { command, int, int };

/* Command processing functions */
inline void process_MoveToLevel(int level, int transitionTime){
    if(level >= MinLevel && level <= MaxLevel){
        cluster_state = MovingToLevel;
        CurrentLevel = level;
        RemainingTime = transitionTime;
    }
}

inline void process_Move(int rate){
    if(rate > 0){
        cluster_state = Moving;
        Rate = rate;
    }
}

inline void process_Step(int stepSize, int transitionTime){
    if(stepSize > 0){
        cluster_state = Stepping;
        StepSize = stepSize;
        RemainingTime = transitionTime;
    }
}

inline void process_Stop(){
    if(cluster_state == MovingToLevel){
        cluster_state = Stopped;
    } else if (cluster_state == Moving){
        cluster_state = Idle;
    } else if (cluster_state == Stepping){
        cluster_state = Stopped;
    }
    RemainingTime = 0;
}

inline void process_MoveToClosestFrequency(){
    cluster_state = MovingToFrequency;
}


/* Main cluster state machine process */
active proctype ClusterStateMachine() {
    command cmd;
    int param1, param2;
    
    do
    :: user_commands?cmd, param1, param2 ->
        if
        :: cmd == MoveToLevel -> process_MoveToLevel(param1, param2);
        :: cmd == Move -> process_Move(param1);
        :: cmd == Step -> process_Step(param1, param2);
        :: cmd == Stop -> process_Stop();
        :: cmd == MoveToClosestFrequency -> process_MoveToClosestFrequency();
        fi;
    :: cluster_state == MovingToLevel && RemainingTime > 0 -> RemainingTime--;
    :: cluster_state == MovingToLevel && RemainingTime == 0 -> cluster_state = Idle;
    :: cluster_state == Stepping && RemainingTime > 0 -> RemainingTime--;
    :: cluster_state == Stepping && RemainingTime == 0 -> cluster_state = Idle;
    :: cluster_state == MovingToFrequency -> cluster_state = Idle;
    od
}

/* User process for command simulation */
proctype User(byte uid) {
    do
    :: user_commands!MoveToLevel, 50, 10;
    :: user_commands!Move, 10;
    :: user_commands!Step, 5, 5;
    :: user_commands!Stop;
    :: user_commands!MoveToClosestFrequency;
    od
}

/* LTL properties from FSM specification */
ltl properties {
    G (cluster_state == Idle -> CurrentLevel >= MinLevel && CurrentLevel <= MaxLevel);
    G (cluster_state == MovingToLevel -> RemainingTime >= 0);
    G (cluster_state == Stepping -> RemainingTime >= 0 && StepSize > 0);
    G (cluster_state == Stopped -> RemainingTime == 0);
}

init {
    atomic {
        run ClusterStateMachine();
        run User(0);
    }
}