---- MODULE ScenesManagementCluster ----
EXTENDS Naturals, Sequences, FiniteSets, TLC

\* Matter Scenes Management Cluster Specification
\* Cluster ID: 0x0062
\* Generated: 2025-09-03T15:03:42.578855

\* Constants
CONSTANTS
    MAX_USERS,           \* Maximum concurrent users
    MAX_COMMANDS,        \* Maximum pending commands
    TIMEOUT_DURATION     \* Command timeout duration

\* Variables
VARIABLES
    cluster_state,       \* Current cluster state: {"SceneTableInitialized", "AddingScene", "ViewingScene", "RemovingScene", "RemovingAllScenes", "StoringScene", "RecallingScene", "GettingSceneMembership", "CopyingScene"}
    attribute_values,    \* Attribute value mappings
    pending_commands,    \* Queue of pending commands
    user_sessions,       \* Active user sessions
    event_history,       \* Generated events history
    error_conditions     \* Current error conditions

\* Type definitions
ClusterState == {"SceneTableInitialized", "AddingScene", "ViewingScene", "RemovingScene", "RemovingAllScenes", "StoringScene", "RecallingScene", "GettingSceneMembership", "CopyingScene"}
AttributeType == {"SceneTableSize", "FabricSceneInfo"}
CommandType == {"AddScene", "ViewScene", "RemoveScene", "RemoveAllScenes", "StoreScene", "RecallScene", "GetSceneMembership", "CopyScene"}

\* Initial state predicate
Init ==
    /\ cluster_state = "SceneTableInitialized"
    /\ attribute_values = [attr \in AttributeType |-> "default"]
    /\ pending_commands = <<>>
    /\ user_sessions = {}
    /\ event_history = <<>>
    /\ error_conditions = {}

\* Transition: SceneTableInitialized -> AddingScene
AddSceneAction ==
    /\ cluster_state = "SceneTableInitialized"
    /\ SceneTableSize < 254
    /\ cluster_state' = "AddingScene"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: SceneTableInitialized -> ViewingScene
ViewSceneAction ==
    /\ cluster_state = "SceneTableInitialized"
    /\ Scene exists
    /\ cluster_state' = "ViewingScene"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: SceneTableInitialized -> RemovingScene
RemoveSceneAction ==
    /\ cluster_state = "SceneTableInitialized"
    /\ Scene exists
    /\ cluster_state' = "RemovingScene"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: SceneTableInitialized -> RemovingAllScenes
RemoveAllScenesAction ==
    /\ cluster_state = "SceneTableInitialized"
    /\ TRUE
    /\ cluster_state' = "RemovingAllScenes"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: SceneTableInitialized -> StoringScene
StoreSceneAction ==
    /\ cluster_state = "SceneTableInitialized"
    /\ Scene exists
    /\ cluster_state' = "StoringScene"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: SceneTableInitialized -> RecallingScene
RecallSceneAction ==
    /\ cluster_state = "SceneTableInitialized"
    /\ Scene exists
    /\ cluster_state' = "RecallingScene"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: SceneTableInitialized -> GettingSceneMembership
GetSceneMembershipAction ==
    /\ cluster_state = "SceneTableInitialized"
    /\ TRUE
    /\ cluster_state' = "GettingSceneMembership"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: SceneTableInitialized -> CopyingScene
CopySceneAction ==
    /\ cluster_state = "SceneTableInitialized"
    /\ TRUE
    /\ cluster_state' = "CopyingScene"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: AddingScene -> SceneTableInitialized
AddSceneResponseAction ==
    /\ cluster_state = "AddingScene"
    /\ Status == SUCCESS
    /\ cluster_state' = "SceneTableInitialized"
    /\ UNCHANGED <<attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Transition: ViewingScene -> SceneTableInitialized
ViewSceneResponseAction ==
    /\ cluster_state = "ViewingScene"
    /\ TRUE
    /\ cluster_state' = "SceneTableInitialized"
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
    \/ AddSceneAction \/ ViewSceneAction \/ RemoveSceneAction \/ RemoveAllScenesAction \/ StoreSceneAction \/ RecallSceneAction \/ GetSceneMembershipAction \/ CopySceneAction \/ AddSceneResponseAction \/ ViewSceneResponseAction

\* Specification
Spec == Init /\ [][Next]_<<cluster_state, attribute_values, pending_commands, user_sessions, event_history, error_conditions>>

\* Fairness conditions
Fairness == WF_<<cluster_state, attribute_values, pending_commands, user_sessions, event_history, error_conditions>>(Next)

====
