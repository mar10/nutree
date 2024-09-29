class Benchmark:
    def __init__(self, name, *, client: str = "auto"):
        self.name = name
        self.client = client

    def run(self):
        pass

    def save_results(self):
        pass

    def load_results(self):
        pass

    def compare_results(self, other):
        pass

    def __repr__(self):
        return f"<Benchmark {self.name}>"


class BenchmarkManager:
    def __init__(self, *, client: str = "auto"):
        self.client = client
        self.benchmarks = []
        self.results = []

    def add_benchmark(self, benchmark):
        self.benchmarks.append(benchmark)

    # def save_results(self):
    #     with open(self.config["results_file"], "w") as f:
    #         f.write(json.dumps(self.results))
