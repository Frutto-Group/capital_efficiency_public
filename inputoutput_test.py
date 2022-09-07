# IC3 Hackathon: capital-efficiency-in-dc-spot
# Define the input transaction class
class InputTx:
    def __init__(self, itt, itv, ott):
        self.inputtokentype  = itt
        self.inputtokenvalue = itv
        self.outputtokentype = ott
# Populate an input transaction class
InputTx1 = InputTx('BTC',100,'ETH')
# Check if correctly assigned
InputTx1.__dict__
# Create input transaction block as list     
InputTxBlock = [] 
  
# Appending instances to list 
InputTxBlock.append( InputTx('BTC',100,'ETH') )
InputTxBlock.append( InputTx('BTC',200,'ETH') )
InputTxBlock.append( InputTx('BTC',300,'ETH') )
  
# Printing the list objects    
for inobj in InputTxBlock:
    print( inobj.inputtokentype, inobj.inputtokenvalue, inobj.outputtokentype, sep =' ' ) 

# Create Input
Input   = []
Num_ITB = 10;               # No. of transaction blocks in input
Num_ITO = len(InputTxBlock) # No. of transaction class objects in transaction block
# Create List of list
for n_ib in range(Num_ITB):
    Input.append([])
    for n_io in range(Num_ITO): 
        Input[n_ib].append(InputTxBlock[n_io])
        