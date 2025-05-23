import json

class RetrieveTracer:
    def __init__(self):
        self.traces = {
            "meta_graph_phase": {
                "meta_graph": None,
                "initial_retrievals": []
            },
            "iterations": []
        }
    
    def record_meta_phase(self, meta_graph: dict):
        """Record meta graph generation phase"""
        self.traces["meta_graph_phase"]["meta_graph"] = json.dumps(meta_graph, indent=2)
    
    def record_initial_retrieval(self, query: str, results: dict):
        """Record initial retrieval results for each query"""
        self.traces["meta_graph_phase"]["initial_retrievals"].append({
            "query": query,
            "results": json.dumps(results, indent=2)
        })
    
    def record_iteration(self, iteration_num: int):
        """Start recording a new iteration"""
        iteration_trace = {
            "iteration": iteration_num,
            "evaluation": None,
            "exploration_graph_snapshot": None,
            "actions": []
        }
        self.traces["iterations"].append(iteration_trace)
    
    def record_evaluation(self, iteration_num: int, evaluation: dict):
        """Record evaluation results"""
        current_iteration = self.traces["iterations"][iteration_num - 1]
        current_iteration["evaluation"] = json.dumps(evaluation, indent=2)
    
    def record_exploration_snapshot(self, iteration_num: int, snapshot: dict):
        """Record exploration graph snapshot"""
        current_iteration = self.traces["iterations"][iteration_num - 1]
        current_iteration["exploration_graph_snapshot"] = json.dumps(snapshot, indent=2)
    
    def record_action(self, iteration_num: int, action: dict, results: dict):
        """Record each retrieval action and its results"""
        current_iteration = self.traces["iterations"][iteration_num - 1]
        current_iteration["actions"].append({
            "action": json.dumps(action, indent=2),
            "results": json.dumps(results, indent=2)
        })
    
    def get_traces(self):
        return self.traces