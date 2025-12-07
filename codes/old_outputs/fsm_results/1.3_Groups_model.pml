/*
 * Promela Model for Matter Groups Cluster
 * Cluster ID: 0x0004
 * Generated: 2025-09-17T07:28:51.307212
 * For verification with SPIN model checker
 */

#define MAX_USERS 3
#define MAX_COMMANDS 5

/* Command types */
mtype = { addgroup, viewgroup, getgroupmembership, removegroup, removeallgroups, addgroupifidentifying };

/* State enumeration */
mtype = { initialized };

/* Global variables */
mtype cluster_state = initialized;
byte active_users = 0;
bool error_condition = false;
chan user_commands = [MAX_COMMANDS] of { mtype, byte };

/* Main cluster state machine */
active proctype ClusterStateMachine() {
    mtype cmd;
    byte user_id;
    
    cluster_state = initialized;
    
    do
    :: user_commands?cmd, user_id ->
        atomic {
            if            :: (cluster_state == initialized && cmd == addgroup) ->
                cluster_state = initialized;
                printf("Transition: initialized -> initialized\n");
            :: (cluster_state == initialized && cmd == viewgroup) ->
                cluster_state = initialized;
                printf("Transition: initialized -> initialized\n");
            :: (cluster_state == initialized && cmd == getgroupmembership) ->
                cluster_state = initialized;
                printf("Transition: initialized -> initialized\n");
            :: (cluster_state == initialized && cmd == removegroup) ->
                cluster_state = initialized;
                printf("Transition: initialized -> initialized\n");
            :: (cluster_state == initialized && cmd == removeallgroups) ->
                cluster_state = initialized;
                printf("Transition: initialized -> initialized\n");
            :: (cluster_state == initialized && cmd == addgroupifidentifying) ->
                cluster_state = initialized;
                printf("Transition: initialized -> initialized\n");
            :: else ->
                printf("Invalid transition or command\n");
            fi
        }
    :: timeout ->
        if
        :: (cluster_state != initialized) ->
            cluster_state = initialized;
            printf("Timeout: returning to initial state\n");
        :: else ->
            skip;
        fi
    od
}

/* User process */
proctype User(byte uid) {
    do
    :: user_commands!addgroup, uid;
    :: user_commands!viewgroup, uid;
    :: skip;
    od
}

/* LTL properties */
ltl safety { [](cluster_state == initialized || cluster_state == initialized) }
ltl liveness { []<>(cluster_state == initialized) }

init {
    atomic {
        run ClusterStateMachine();
        run User(0);
    }
}
