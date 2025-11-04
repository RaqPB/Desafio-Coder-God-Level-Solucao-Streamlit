# Função para corrigir o nome da loja
def formatar_nome_loja(nome_invertido):
    """
    Formata o nome da loja, tentando priorizar o nome comercial (última parte) 
    e removendo ruídos legais ou siglas do contexto.
    """
    if ' - ' in nome_invertido:
        partes = nome_invertido.split(' - ')
        
        if len(partes) >= 2:
            nome_principal = partes[-1].strip()
            contexto_list = partes[:-1]
            
            # --- NOISE CLEANING E FILTRAGEM ---
            ruido_legal = ['ME', 'S.A.', 'LTDA', 'EIRELI', 'EPP', 'EI', 'FILHOS']
            contexto_limpo = []
            
            for parte in contexto_list:
                limpa = parte.strip()
                # Remove o ruído se a parte for exatamente uma sigla legal em maiúsculas
                if limpa.upper() not in ruido_legal and len(limpa) > 0:
                    contexto_limpo.append(limpa)
            
            contexto = " ".join(contexto_limpo).strip()
            
            # CONDICIONAL: Se o contexto se tornou vazio após a limpeza, não use parênteses.
            if not contexto:
                return nome_principal
            else:
                # Retorna o nome principal seguido do contexto limpo
                return f"{nome_principal} {contexto}"
            
    # Se não houver separação, retorna o nome original (ex: 'Loja X')
    return nome_invertido
