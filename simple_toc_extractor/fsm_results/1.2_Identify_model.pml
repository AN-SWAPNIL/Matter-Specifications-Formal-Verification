/*
 * Promela Model for Matter Identify Cluster
 * Cluster ID: 0x0003
 * Generated: 2025-09-03T15:03:09.209862
 * For verification with SPIN model checker
 */

#define MAX_USERS 3
#define MAX_COMMANDS 5

/* Message types */
mtype = { identify, triggereffect };

/* State enumeration */
mtype = { idle, identifying, effectinprogress };

/* Global variables */
mtype cluster_state = idle;
byte active_users = 0;
bool error_condition = false;
chan user_commands = [MAX_COMMANDS] of { mtype, byte };
chan cluster_events = [MAX_COMMANDS] of { mtype, byte };
chan security_alerts = [MAX_COMMANDS] of { mtype, byte };

/* User session structure */
typedef UserSession {
    bool authenticated;
    byte role;
    byte session_id;
};

UserSession users[MAX_USERS];

/* Security context */
typedef SecurityContext {
    byte threat_level;
    bool access_granted;
};

SecurityContext security;

/* Initialize cluster */
inline init_cluster() {
    cluster_state = idle;
    error_condition = false;
    security.threat_level = 0;
    security.access_granted = true;
}

/* Process command with security checks */
inline process_command(cmd, user_id) {
    if
    :: (users[user_id].authenticated && security.access_granted) ->
        atomic {
            if
            :: (cluster_state == idle) ->
                cluster_state = identifying;
                cluster_events ! identify(identifytime_>_0), user_id;
            :: (cluster_state == identifying) ->
                cluster_state = idle;
                cluster_events ! identifytime_reaches_0, user_id;
            :: (cluster_state == idle) ->
                cluster_state = effectinprogress;
                cluster_events ! triggereffect, user_id;
            :: (cluster_state == identifying) ->
                cluster_state = effectinprogress;
                cluster_events ! triggereffect, user_id;
            :: (cluster_state == effectinprogress) ->
                cluster_state = idle;
                cluster_events ! effect_completes_or_triggereffect(stopeffect), user_id;
            :: (cluster_state == effectinprogress) ->
                cluster_state = identifying;
                cluster_events ! triggereffect(finisheffect), user_id;
            :: else -> 
                security_alerts ! error, user_id;
            fi
        }
        cluster_state = identifying;
        cluster_events ! cmd, user_id;
    :: else -> 
        security_alerts ! error, user_id;
    fi
}

/* User authentication process */
proctype UserAuth(byte uid) {
    users[uid].session_id = uid;
    
    do
    :: atomic {
        if
        :: (active_users < MAX_USERS) ->
            users[uid].authenticated = true;
            users[uid].role = 1; /* default user role */
            active_users++;
            break;
        :: else ->
            printf("Max users reached\n");
            break;
        fi
    }
    od;
    
    /* User activity loop */
    do
    :: user_commands ? cmd, _ ->
        process_command(cmd, uid);
    :: timeout ->
        users[uid].authenticated = false;
        active_users--;
        break;
    od
}

/* Cluster state machine */
proctype ClusterStateMachine() {
    mtype cmd;
    byte user_id;
    
    init_cluster();
    
    do
    :: user_commands ? cmd, user_id ->
        process_command(cmd, user_id);
    :: timeout ->
        if
        :: (cluster_state == processing) ->
            cluster_state = error;
            security_alerts ! timeout, 0;
        :: else -> skip;
        fi
    :: (cluster_state == error) ->
        cluster_state = idle;
        printf("Cluster recovered from error\n");
    od
}

/* Security monitor */
proctype SecurityMonitor() {
    mtype alert_type;
    byte context;
    
    do
    :: security_alerts ? alert_type, context ->
        security.threat_level++;
        if
        :: (security.threat_level > 3) ->
            printf("CRITICAL SECURITY THREAT DETECTED\n");
            security.access_granted = false;
        :: else -> skip;
        fi
    :: timeout ->
        if
        :: (security.threat_level > 0) ->
            security.threat_level--;
        :: else -> skip;
        fi
    od
}

/* LTL Properties for verification */
ltl safety1 { [](cluster_state == processing -> <>(cluster_state == idle || cluster_state == error)) }
ltl safety2 { []((active_users > 0) -> <>(active_users == 0)) }
ltl security1 { [](security.threat_level == 4 -> <>security.threat_level < 4) }
ltl liveness1 { []<>(cluster_state == idle) }

/* Main process */
init {
    atomic {
        run ClusterStateMachine();
        run SecurityMonitor();
        run UserAuth(0);
        run UserAuth(1);
    }
}
