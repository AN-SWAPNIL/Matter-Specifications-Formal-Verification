---- MODULE OnOffCluster ----
EXTENDS Naturals, Sequences, FiniteSets, TLC

\* Matter On/Off Cluster Specification
\* Cluster ID: 0x0006
\* Generated: 2025-09-03T15:04:29.072397

\* Constants
CONSTANTS
    MAX_USERS,           \* Maximum concurrent users
    MAX_COMMANDS,        \* Maximum pending commands
    TIMEOUT_DURATION     \* Command timeout duration

\* Variables
VARIABLES
    cluster_state,       \* Current cluster state: {"Off", "On", "TimedOn", "DelayedOff"}
    attribute_values,    \* Attribute value mappings
    pending_commands,    \* Queue of pending commands
    user_sessions,       \* Active user sessions
    event_history,       \* Generated events history
    error_conditions     \* Current error conditions

\* Type definitions
ClusterState == {"Off", "On", "TimedOn", "DelayedOff"}
AttributeType == {"OnOff", "GlobalSceneControl", "OnTime", "OffWaitTime", "StartUpOnOff"}
CommandType == {"On", "Off", "Toggle", "OffWithEffect", "OnWithRecallGlobalScene", "OnWithTimedOff"}

\* Initial state predicate
Init ==
    /\ cluster_state = "Off"
    /\ attribute_values = [attr \in AttributeType |-> "default"]
    /\ pending_commands = <<>>
    /\ user_sessions = {}
    /\ event_history = <<>>
    /\ error_conditions = {}

\* Transition: Off -> On
OnAction ==
    /\ cluster_state = "Off"
    /\ !OFFONLY
    /\ cluster_state' = "On"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: Off -> On
ToggleAction ==
    /\ cluster_state = "Off"
    /\ !OFFONLY
    /\ cluster_state' = "On"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: Off -> Off
OffAction ==
    /\ cluster_state = "Off"
    /\ TRUE
    /\ cluster_state' = "Off"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: On -> Off
OffAction ==
    /\ cluster_state = "On"
    /\ TRUE
    /\ cluster_state' = "Off"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: On -> Off
OffWithEffectAction ==
    /\ cluster_state = "On"
    /\ LT
    /\ cluster_state' = "Off"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: On -> Off
ToggleAction ==
    /\ cluster_state = "On"
    /\ !OFFONLY
    /\ cluster_state' = "Off"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: Off -> On
OnWithRecallGlobalSceneAction ==
    /\ cluster_state = "Off"
    /\ LT
    /\ cluster_state' = "On"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: On -> TimedOn
OnWithTimedOffAction ==
    /\ cluster_state = "On"
    /\ LT
    /\ cluster_state' = "TimedOn"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: TimedOn -> DelayedOff
OnTimetimerexpiresAction ==
    /\ cluster_state = "TimedOn"
    /\ OnTime == 0
    /\ cluster_state' = "DelayedOff"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: DelayedOff -> Off
OffWaitTimetimerexpiresAction ==
    /\ cluster_state = "DelayedOff"
    /\ OffWaitTime == 0
    /\ cluster_state' = "Off"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Safety properties
TypeInvariant ==
    /\ cluster_state \in ClusterState
    /\ \A attr \in DOMAIN attribute_values : attr \in AttributeType
    /\ Len(pending_commands) <= MAX_COMMANDS

SafetyInvariant ==
    /\ cluster_state \in ClusterState
    /\ (cluster_state = "Error") => (Cardinality(error_conditions) > 0)

\* Liveness properties
EventualProgress ==
    /\ (cluster_state = "Processing") ~> (cluster_state \in {"Ready", "Error"})

\* Next state relation
Next ==
    \/ OnAction \/ ToggleAction \/ OffAction \/ OffAction \/ OffWithEffectAction \/ ToggleAction \/ OnWithRecallGlobalSceneAction \/ OnWithTimedOffAction \/ OnTimetimerexpiresAction \/ OffWaitTimetimerexpiresAction

\* Specification
Spec == Init /\ [][Next]_<<cluster_state, attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Fairness conditions
Fairness == WF_<<cluster_state, attribute_values, pending_commands, user_sessions, event_history, error_conditions>>(Next)

====
