from .classes.token_class import Token
from .constants.token_specs import token_specs, MULTICHAR_OPS
from .classes.sourceSpan import SourceSpan

#############################################################################
# Function name:        tokenize                                            #
# Description:          Converts source code into a list of token objects   #
#                       by scanning and categorizing each lexeme            #
# Parameters:    str –  source: source code to be tokenized                 #
# Return Value: list – tokens: list of generated Token objects              #
#############################################################################
def tokenize(source):
    tokens = []
    i = 0
    line = 1
    col = 1

    while i < len(source):

        term = source[i]

        # Tokenize a number                                                                 
        if term.isdigit():                                                                  
            start = i                                                                       
            dot_seen = False                                                                
                                                                                                                                                                  
            # Loop over term until nondigit                                                 
            while i < len(source) and (source[i].isdigit() or                               
                                       (source[i] == "." and dot_seen == False)):           
                                                                                  
                if source[i] == ".":                                                        
                    dot_seen = True                                                         
                                                                                         
                i += 1                                                                      
                col += 1                                                                    
                                                                                           
            term = source[start:i]                                                          
            start_col = col - len(term)                                                     
                                                                                           
            if dot_seen == True:                                                            
                tokens.append(Token("FLOAT_LIT", term, SourceSpan(line, start_col, col-1)))                     
            else:                                                                           
                tokens.append(Token("INT_LIT", term, SourceSpan(line, start_col, col-1)))                   
            continue                                                                        
                                                                                           
        # Tokenize keywords, chars, identifiers                                             
        elif term.isalpha() or term == "_":                                                 
            start = i                                                                       
                                                                                         
            # Loop over term until whitespace                                               
            while i < len(source) and (source[i].isalpha() or                              
                                       source[i] == "_" or                                 
                                       source[i].isdigit()):                                
                i += 1                                                                      
                col += 1                                                                    
                                                                                         
            term = source[start:i]                                                          
            start_col = col - len(term)                                                     
                                                                                        
            if term in token_specs:                                                  
                category = token_specs[term]                                                
                token = Token(category, term, SourceSpan(line, start_col, col-1))                           
                tokens.append(token)                                                        
            else:                                                                                                                              
                token = Token("IDENTIFIER", term, SourceSpan(line, start_col, col-1))                          
                tokens.append(token)                                                        
            continue                                                                        

        # Tokenize character literals                                                       
        elif term == "'":                                                                   
            start_col = col                                                                 
            i += 1                                                                          
                                                                                       
            if i < len(source):                                                             
                char_literal = source[i]                                                    
                i += 1                                                                      
                                                                                       
                if i < len(source) and source[i] == "'":                                    
                    i += 1                                                                  
                    tokens.append(Token("CHAR_LITERAL", char_literal, SourceSpan(line, start_col, start_col + 2)))  
                    col += 3
                    continue                                                                
                else:                                                                       
                    raise SyntaxError(f"Unclosed char literal at line {line}, column {start_col}")                              
                                                                                      
            else:                                                                           
                raise SyntaxError(f"Empty char literal at line {line}, column {start_col}")                                     
                                                                                           
        #Code comments. Check if starting term and second term together == '//'             
        elif (term == '/') and ((i + 1) < len(source)) and (source[i + 1] == '/'):                
            i += 2                                                                          
            col += 2                                                                        
                                                                                           
            #skip over commented line until newline                                         
            while (i < len(source) and source[i] != '\n'):                                  
                i += 1                                                                      
                col += 1                                                                    
                                                                                           
            continue                                                                        
                                                                                           
        #Skip whitespace (compiler doesn't need to know this)                               
        elif term.isspace():                                                                
            if term == '\n':                                                                
                line += 1                                                                   
                col = 1                                                                     
            else:                                                                           
                col += 1                                                                    
                                                                                          
            i += 1                                                                          
            continue                                                                        
                                                                                           
        #Evaluate for operators
        elif (i + 1 < len(source)) and (source[i:i+2] in MULTICHAR_OPS):
            term = source[i:i+2]
            category = token_specs[term]
            tokens.append(Token(category, term, SourceSpan(line, col, col + 1)))
            i += 2
            col += 2
            continue

        elif term in token_specs:
            category = token_specs[term]
            tokens.append(Token(category, term, SourceSpan(line, col, col)))
            i += 1
            col += 1
            continue

        else:
           term = source[i]
           raise SyntaxError(f"Unexpected character : '{term}' at line {line}, column {col}")

    return tokens