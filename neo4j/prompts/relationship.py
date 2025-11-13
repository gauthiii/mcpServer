prompt = f'''

    Create a relationship for the following.

    Steve from label Person has "FRIENDS_WITH" to Peter.


    (:Person {{name: str}})-[:FRIENDS_WITH]->(:Person {{name: str}})

    






'''