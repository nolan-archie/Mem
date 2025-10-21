                

from core.memory_rag import MR

import pprint



     

entry = MR.add_memory("Mainmi loves watching the stars at night.", tags=["personal"])

print("Added:", entry)



        

res = MR.search("stars", k=5)

print("\nSearch results:")

pprint.pprint(res)



       

print("\nTotal memories:", len(MR.list_memories()))



                          

print("\nRe-embedding all memories (this may take a while)...")

print(MR.reembed_all())

