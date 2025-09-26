/*
 * Promela Model for Matter Identify Cluster
 * Cluster ID: 0x0003
 * Generated: 2025-09-26T18:53:25.772649
 * For verification with SPIN model checker
 */

#define MAX_USERS 3
#define MAX_COMMANDS 5

/* Command types */
mtype = { nop };

/* State enumeration */
mtype = { uninitialized, ready, error };

/* Global variables */
mtype cluster_state = uninitialized;
byte active_users = 0;
bool error_condition = false;
chan user_commands = [MAX_COMMANDS] of { mtype, byte };

/* Main cluster state machine */
active proctype ClusterStateMachine() {
    mtype cmd;
    byte user_id;
    
    cluster_state = uninitialized;
    
    do
    :: user_commands?cmd, user_id ->
        atomic {
            if            :: (cluster_state == uninitialized && cmd == nop) ->
                cluster_state = ready;
                printf("Transition: uninitialized -> ready\n");
            :: else ->
                printf("Invalid transition or command\n");
            fi
        }
    :: timeout ->
        if
        :: (cluster_state != uninitialized) ->
            cluster_state = uninitialized;
            printf("Timeout: returning to initial state\n");
        :: else ->
            skip;
        fi
    od
}

/* User process */
proctype User(byte uid) {
    do
    :: user_commands!nop, uid;
    :: user_commands!nop, uid;
    :: skip;
    od
}

/* LTL properties */
ltl safety { [](cluster_state == uninitialized || cluster_state == ready) }
ltl liveness { []<>(cluster_state == uninitialized) }

init {
    atomic {
        run ClusterStateMachine();
        run User(0);
    }
}
