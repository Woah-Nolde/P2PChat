import tomllib
import tomli_w

def load_config(path="config/config.toml"):
    with open(path, "rb") as f:
        return tomllib.load(f)

def dump_config(config):
    with open("config/config.toml", "wb") as f:  # "wb" (binary mode)
        tomli_w.dump(config, f)