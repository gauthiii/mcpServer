promptx = f'''

    Which of the nodes are involved in the "ALIGNS_WITH" relationship

    Mention which label and names of those nodes.

    No additional information or unnecessary explanations



'''


prompt = f'''

    Find how movies (label: Movies) has been directed by Lokesh (label: Director) .

    Once you fetch them and get the results.

    in the end show it in this format

    () - [] -> ()



'''



prompt1 = f'''

    Find all the nodes and the relationships

    for the labels: "Director" and "Movies"

    Once you fetch them and get the results.

    in the end show it in this schema:

    (:Director) - [:DIRECTED] -> (:Movies)



'''


prompt2 = f'''

    Find all the nodes and the relationships

    for the labels: "Person"

    Once you fetch them and get the results.

    in the end show it in this format

    () - [] -> ()



'''




prompt3 = f'''

    Find all the nodes and the relationships

    for the labels: "Person"

    where only "Alice" is involved.

    Once you fetch them and get the results.

    in the end show it in this format

    () - [] -> ()



'''


prompt4 =f'''

### Schemas:

```
(:Director {{name: str}})-[:DIRECTED]->(:Movies {{name: str}})
(:Person {{name: str}})-[:FRIENDS_WITH]->(:Person {{name: str}})
(:Person {{name: str}})-[:LIKES_WATCHING]->(:Movies {{name: str}})
```


### Question

Find me the movies which are directed by Lokesh and who likes watching those movies?




'''