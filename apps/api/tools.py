def search_tool(query: str):
    return f'Search result for {query}'

def browser_tool(url: str):
    return f'Browsed {url} - scraped content placeholder'

def file_tool(action: str, path: str):
    return f'{action} on {path}'