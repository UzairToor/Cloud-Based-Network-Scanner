import asyncio
import random
import time

class VirtualServer:
    def __init__(self, server_id: str):
        self.server_id = server_id
        self.active_connections = 0
        self.cpu_load = random.uniform(1.0, 5.0)  # Base CPU load
        self.memory_usage = random.uniform(10.0, 20.0)  # Base Memory
        self.total_storage_gb = 100.0
        self.free_storage_gb = random.uniform(70.0, 95.0)

    def process_tick(self):
        # connections drop over time as requests complete
        completed = min(self.active_connections, random.randint(5, 15))
        self.active_connections -= completed
        
        # Recalculate metrics based on connections
        # Let's say each connection adds roughly 0.5% CPU load and 0.1% Mem
        base_cpu = random.uniform(1.0, 5.0)
        self.cpu_load = min(100.0, base_cpu + (self.active_connections * 0.8))
        
        base_mem = random.uniform(10.0, 20.0)
        self.memory_usage = min(100.0, base_mem + (self.active_connections * 0.2))

        # Randomize free storage slightly for realism
        if random.random() > 0.8:
            self.free_storage_gb = max(0.0, self.free_storage_gb - random.uniform(-0.1, 0.5))
            if self.free_storage_gb > self.total_storage_gb:
                self.free_storage_gb = self.total_storage_gb

    def add_connections(self, count: int):
        self.active_connections += count

class ClusterManager:
    def __init__(self):
        self.servers = []
        self.is_running = False
        self.total_requests = 0
        
        # Auto-scaling config
        self.min_servers = 1
        self.max_servers = 10
        self.scale_out_threshold = 75.0  # CPU %
        self.scale_in_threshold = 20.0   # CPU %
        
        self.add_server() # Start with 1 server

    def add_server(self):
        if len(self.servers) < self.max_servers:
            sid = f"Server-{len(self.servers) + 1}-{random.randint(1000, 9999)}"
            self.servers.append(VirtualServer(sid))

    def remove_server(self):
        if len(self.servers) > self.min_servers:
            # Try to remove the server with the least connections
            self.servers.sort(key=lambda s: s.active_connections)
            # Before removing, we could simulate connection draining, but for simplicity we just drop it
            self.servers.pop(0)

    def route_traffic(self, connections: int):
        self.total_requests += connections
        if not self.servers:
            return
            
        # Distribute connections using Least Connections algorithm
        # This ensures the load is perfectly balanced across all servers
        for _ in range(connections):
            # Find the server with the minimum active connections
            least_loaded_server = min(self.servers, key=lambda s: s.active_connections)
            least_loaded_server.add_connections(1)

    def tick(self):
        if not self.is_running:
            return

        total_cpu = 0
        for server in self.servers:
            server.process_tick()
            total_cpu += server.cpu_load

        # Auto Scaling logic
        if self.servers:
            avg_cpu = total_cpu / len(self.servers)
            
            # Very simple auto-scaling cooldown simulation (it just scales 1 per tick if needed)
            if avg_cpu > self.scale_out_threshold:
                self.add_server()
            elif avg_cpu < self.scale_in_threshold:
                self.remove_server()

    def get_status(self):
        servers_data = [
            {
                "id": s.server_id,
                "connections": s.active_connections,
                "cpu": round(s.cpu_load, 1),
                "memory": round(s.memory_usage, 1),
                "free_storage": round(s.free_storage_gb, 1),
                "total_storage": round(s.total_storage_gb, 1)
            }
            for s in self.servers
        ]
        
        avg_cpu = sum(s["cpu"] for s in servers_data) / len(servers_data) if servers_data else 0
        
        return {
            "is_running": self.is_running,
            "total_requests": self.total_requests,
            "active_servers_count": len(self.servers),
            "average_cpu": round(avg_cpu, 1),
            "servers": servers_data
        }

# Global instance for the FastAPI app
cluster_manager = ClusterManager()

async def simulation_loop():
    while True:
        try:
            cluster_manager.tick()
        except Exception as e:
            print(f"Simulation tick error: {e}")
        await asyncio.sleep(2) # 2 seconds tick
