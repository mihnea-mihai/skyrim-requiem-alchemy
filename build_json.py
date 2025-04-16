import csv
import json

with open("alchemy.csv", "r") as file:
    data = [row for row in csv.DictReader(file)]

with open("alchemy.json", "w") as file:
    json.dump(data, file, indent=4)
