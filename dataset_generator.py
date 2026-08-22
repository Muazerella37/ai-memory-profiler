import json
import random
import uuid
# ==========================================
# CONFIGURATION
# ==========================================
TARGET_EVENTS = 10000
LEAK_PROBABILITY = 0.10
OUTPUT_FILENAME = "memory_logs.jsonl"
class MemoryLeakSimulator:
    def __init__(self):
        self.tick = 0
        self.events = []
        self.active_entities = {}
        
    def generate_hex_id(self):
        return uuid.uuid4().hex
        
    def generate_address(self):
        # Generate a mock memory address (e.g., 0x7f8a9b0c1d2e)
        return "0x" + uuid.uuid4().hex[:12]
        
    def add_event(self, action, entity):
        event = {
            "tick": self.tick,
            "event_id": self.generate_hex_id(),
            "action": action,
            "entity_id": entity["entity_id"],
            "entity_type": entity["entity_type"],
            "parent_id": entity["parent_id"],
            "memory_address": entity["memory_address"],
            "size_bytes": entity["size_bytes"],
            "is_leak": entity.get("is_leak", False)
        }
        self.events.append(event)
        
    def allocate_entity(self, entity_type, parent_id=None):
        self.tick += 1
        
        entity = {
            "entity_id": self.generate_hex_id(),
            "entity_type": entity_type,
            "parent_id": parent_id,
            "memory_address": self.generate_address(),
            "size_bytes": random.randint(16, 8192),
            "children": [],
            "is_leak": False
        }
        
        self.active_entities[entity["entity_id"]] = entity
        self.add_event("ALLOCATE", entity)
        
        # Link to parent if applicable
        if parent_id and parent_id in self.active_entities:
            self.active_entities[parent_id]["children"].append(entity["entity_id"])
            
        return entity["entity_id"]
        
    def destroy_entity_tree(self, root_id):
        if root_id not in self.active_entities:
            return
            
        # 1. Gather the parent and all descendants
        descendants = []
        def gather_children(ent_id):
            ent = self.active_entities.get(ent_id)
            if not ent: return
            for child_id in ent["children"]:
                descendants.append(child_id)
                gather_children(child_id)
                
        gather_children(root_id)
        
        leaked_entities = set()
        
        # ==========================================
        # LEAK INJECTOR LOGIC
        # ==========================================
        # In a healthy lifecycle, destroying a parent means all children 
        # are logically destroyed and their memory is freed.
        #
        # To simulate a memory leak (orphan objects) for LLM fine-tuning, 
        # we apply a leak probability. If triggered, we simulate a bug where 
        # the parent is destroyed, but one or more of its children fail to 
        # have their memory freed (missing FREE_MEMORY event).
        # We flag these specific orphaned entities with `is_leak=True`.
        # ==========================================
        if descendants and random.random() < LEAK_PROBABILITY:
            # Pick a random number of children to leak
            num_to_leak = random.randint(1, len(descendants))
            leaked_entities = set(random.sample(descendants, num_to_leak))
            
            for le_id in leaked_entities:
                self.active_entities[le_id]["is_leak"] = True
                
                # Retroactively label previous events (e.g. ALLOCATE) for this entity 
                # as part of a leak sequence so the LLM has perfect supervision.
                for ev in reversed(self.events):
                    if ev["entity_id"] == le_id:
                        ev["is_leak"] = True
        all_to_destroy = [root_id] + descendants
        
        # 2. DESTROY phase (Logical deletion for all entities in the tree)
        self.tick += 1
        for ent_id in all_to_destroy:
            self.add_event("DESTROY", self.active_entities[ent_id])
            
        # 3. FREE_MEMORY phase (Actual RAM cleanup)
        self.tick += 1
        for ent_id in all_to_destroy:
            if ent_id not in leaked_entities:
                self.add_event("FREE_MEMORY", self.active_entities[ent_id])
                
        # 4. Remove from active tracking
        for ent_id in all_to_destroy:
            del self.active_entities[ent_id]
            
    def step(self):
        # Simulate game loop activity progression
        self.tick += random.randint(1, 5)
        
        # A. Allocate root entities (e.g., new players, navmeshes joining the scene)
        for _ in range(random.randint(1, 3)):
            self.allocate_entity(random.choice(["Player", "NPC", "NavMesh", "AudioBuffer"]))
            
        # B. Allocate child entities (e.g., players shooting weapons or spawning particles)
        existing_roots = [e for e in self.active_entities.values() if e["parent_id"] is None]
        for root in existing_roots:
            if random.random() < 0.3:
                self.allocate_entity(random.choice(["Weapon", "Particle"]), parent_id=root["entity_id"])
                
        # C. Destroy entities (e.g., players disconnecting, particles expiring)
        # Keep a healthy population size so we naturally build tree depth
        if len(existing_roots) > 15:
            num_to_destroy = random.randint(1, 4)
            roots_to_destroy = random.sample(existing_roots, num_to_destroy)
            for root in roots_to_destroy:
                self.destroy_entity_tree(root["entity_id"])
                
    def run_simulation(self):
        print(f"Starting simulation. Target events: {TARGET_EVENTS}")
        
        while len(self.events) < TARGET_EVENTS:
            self.step()
            
        # Ensure we don't exceed the requested size due to batch additions
        self.events = self.events[:TARGET_EVENTS]
        
        # Write dataset to JSONL
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            for ev in self.events:
                f.write(json.dumps(ev) + "\n")
                
        print(f"Successfully generated {len(self.events)} memory log events in '{OUTPUT_FILENAME}'")
if __name__ == "__main__":
    simulator = MemoryLeakSimulator()
    simulator.run_simulation()