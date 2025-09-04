---- MODULE GroupsCluster ----
EXTENDS Naturals, Sequences, FiniteSets, TLC

\* Matter Groups Cluster Specification
\* Cluster ID: 0x0004
\* Generated: 2025-09-03T15:03:25.705780

\* Constants
CONSTANTS
    MAX_USERS,           \* Maximum concurrent users
    MAX_COMMANDS,        \* Maximum pending commands
    TIMEOUT_DURATION     \* Command timeout duration

\* Variables
VARIABLES
    cluster_state,       \* Current cluster state: {"Initialized", "AddingGroup", "ViewingGroup", "GettingMembership", "RemovingGroup", "RemovingAllGroups", "AddingGroupIfIdentifying"}
    attribute_values,    \* Attribute value mappings
    pending_commands,    \* Queue of pending commands
    user_sessions,       \* Active user sessions
    event_history,       \* Generated events history
    error_conditions     \* Current error conditions

\* Type definitions
ClusterState == {"Initialized", "AddingGroup", "ViewingGroup", "GettingMembership", "RemovingGroup", "RemovingAllGroups", "AddingGroupIfIdentifying"}
AttributeType == {"NameSupport"}
CommandType == {"AddGroup", "ViewGroup", "GetGroupMembership", "RemoveGroup", "RemoveAllGroups", "AddGroupIfIdentifying"}

\* Initial state predicate
Init ==
    /\ cluster_state = "Initialized"
    /\ attribute_values = [attr \in AttributeType |-> "default"]
    /\ pending_commands = <<>>
    /\ user_sessions = {}
    /\ event_history = <<>>
    /\ error_conditions = {}

\* Transition: Initialized -> AddingGroup
AddGroupAction ==
    /\ cluster_state = "Initialized"
    /\ TRUE
    /\ cluster_state' = "AddingGroup"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: Initialized -> ViewingGroup
ViewGroupAction ==
    /\ cluster_state = "Initialized"
    /\ TRUE
    /\ cluster_state' = "ViewingGroup"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: Initialized -> GettingMembership
GetGroupMembershipAction ==
    /\ cluster_state = "Initialized"
    /\ TRUE
    /\ cluster_state' = "GettingMembership"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: Initialized -> RemovingGroup
RemoveGroupAction ==
    /\ cluster_state = "Initialized"
    /\ TRUE
    /\ cluster_state' = "RemovingGroup"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: Initialized -> RemovingAllGroups
RemoveAllGroupsAction ==
    /\ cluster_state = "Initialized"
    /\ TRUE
    /\ cluster_state' = "RemovingAllGroups"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: Initialized -> AddingGroupIfIdentifying
AddGroupIfIdentifyingAction ==
    /\ cluster_state = "Initialized"
    /\ TRUE
    /\ cluster_state' = "AddingGroupIfIdentifying"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: AddingGroup -> Initialized
AddGroupResponseAction ==
    /\ cluster_state = "AddingGroup"
    /\ TRUE
    /\ cluster_state' = "Initialized"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: ViewingGroup -> Initialized
ViewGroupResponseAction ==
    /\ cluster_state = "ViewingGroup"
    /\ TRUE
    /\ cluster_state' = "Initialized"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: GettingMembership -> Initialized
GetGroupMembershipResponseAction ==
    /\ cluster_state = "GettingMembership"
    /\ TRUE
    /\ cluster_state' = "Initialized"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: RemovingGroup -> Initialized
RemoveGroupResponseAction ==
    /\ cluster_state = "RemovingGroup"
    /\ TRUE
    /\ cluster_state' = "Initialized"
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
    \/ AddGroupAction \/ ViewGroupAction \/ GetGroupMembershipAction \/ RemoveGroupAction \/ RemoveAllGroupsAction \/ AddGroupIfIdentifyingAction \/ AddGroupResponseAction \/ ViewGroupResponseAction \/ GetGroupMembershipResponseAction \/ RemoveGroupResponseAction

\* Specification
Spec == Init /\ [][Next]_<<cluster_state, attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Fairness conditions
Fairness == WF_<<cluster_state, attribute_values, pending_commands, user_sessions, event_history, error_conditions>>(Next)

====
