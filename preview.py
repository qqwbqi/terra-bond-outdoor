import os, re, json
from flask import Flask, send_from_directory, request, make_response

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_url_path='')

MOCK_SHOP = {
    'name': 'TerraBond Outdoor',
    'description': 'Real bonded stone surfaces for patios, pool decks, and outdoor living spaces.',
    'url': 'http://localhost:9999',
    'locale': 'en',
    'currency': 'USD',
}

MOCK_CART = {'item_count': 0, 'items': [], 'total_price': 0}

MOCK_LINKLISTS = {
    'main-menu': {'links': [
        {'url': '/index.html', 'title': 'Home'},
        {'url': '/sample-kit.html', 'title': 'Sample Kit'},
        {'url': '/diy-test-kit.html', 'title': 'DIY Test Kit'},
        {'url': '/project-estimate.html', 'title': 'Project Estimate'},
        {'url': '/dealer-program.html', 'title': 'Dealer Program'},
        {'url': '/installation-guide.html', 'title': 'Installation'},
        {'url': '/faq.html', 'title': 'FAQ'},
    ]},
}

MOCK_SETTINGS = {
    'color_background': '#FFFFFF',
    'color_sand': '#EAE5D9',
    'color_dark': '#2E2E2E',
    'color_button': '#2A4B3C',
    'color_button_hover': '#1F3A2D',
    'color_accent': '#B8904D',
    'color_text': '#2E2E2E',
    'color_text_light': '#888888',
    'color_border': '#EAE5D9',
    'color_card': '#FFFFFF',
    'page_width': '1280',
    'border_radius': '12',
    'font_body': "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    'font_heading': "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
}

class LiquidRenderer:
    def __init__(self, theme_dir):
        self.theme_dir = theme_dir
    
    def read_file(self, path):
        full = os.path.join(self.theme_dir, path)
        if os.path.exists(full):
            with open(full, 'r', encoding='utf-8') as f:
                return f.read()
        return ''
    
    def render(self, template_name, context=None):
        ctx = context or {}
        ctx['shop'] = MOCK_SHOP
        ctx['cart'] = MOCK_CART
        ctx['linklists'] = MOCK_LINKLISTS
        ctx['settings'] = MOCK_SETTINGS
        ctx['routes'] = {'cart_url': '/cart.html'}
        ctx['section'] = {'settings': {}, 'blocks': [], 'id': 'mock-section'}
        ctx['template'] = template_name.replace('/', '.')
        ctx['page_title'] = ctx.get('page', {}).get('title', 'TerraBond Outdoor')
        
        template_content = self.read_file(f'templates/{template_name}.liquid')
        if not template_content:
            return f'<h1>Template not found: {template_name}</h1>', 404
        
        layout_name = 'theme'
        layout_match = re.search(r'\{%\s*layout\s+[\'"](.+?)[\'"]\s*%\}', template_content)
        if layout_match:
            layout_name = layout_match.group(1)
        
        content_for_layout = re.sub(r'\{%\s*layout\s+[\'"].*?[\'"]\s*%\}\s*\n?', '', template_content, count=1)
        content_for_layout = self.process_sections(content_for_layout, ctx)
        
        if layout_name == 'none':
            return self.process_liquid(content_for_layout, ctx)
        
        layout_content = self.read_file(f'layout/{layout_name}.liquid')
        if not layout_content:
            return self.process_liquid(content_for_layout, ctx)
        
        layout_content = self.process_sections(layout_content, ctx)
        
        ctx['content_for_layout'] = self.process_liquid(content_for_layout, ctx)
        ctx['content_for_header'] = ''
        ctx['content_for_footer'] = ''
        
        final = self.process_liquid(layout_content, ctx)
        return final
    
    def process_sections(self, content, ctx):
        def section_replacer(match):
            section_name = match.group(1).strip()
            section_content = self.read_file(f'sections/{section_name}.liquid')
            if not section_content:
                return f'<!-- Section not found: {section_name} -->'
            section_content = re.sub(r'\{%\s*schema\s*%\}.*?\{%\s*endschema\s*%\}\s*', '', section_content, flags=re.DOTALL)
            return self.process_liquid(section_content, ctx)
        return re.sub(r'\{%\s*section\s+[\'"]([\w\-]+)[\'"]\s*%\}', section_replacer, content, flags=re.DOTALL)
    
    def process_liquid(self, content, ctx):
        # Process render (snippets)
        def render_replacer(match):
            snippet_name = match.group(1).strip()
            params = match.group(2) or ''
            snippet_content = self.read_file(f'snippets/{snippet_name}.liquid')
            if not snippet_content:
                return f'<!-- Snippet not found: {snippet_name} -->'
            
            snippet_ctx = dict(ctx)
            if params:
                for param_match in re.finditer(r'([\w_]+):\s*([^,]+)', params):
                    key = param_match.group(1).strip()
                    val = param_match.group(2).strip().strip('"\'')
                    snippet_ctx[key] = val
            
            return self.process_liquid(snippet_content, snippet_ctx)
        
        content = re.sub(r'\{%\s*render\s+[\'"]([\w\-]+)[\'"]\s*(.*?)%\}', render_replacer, content, flags=re.DOTALL)
        
        # Process capture
        def capture_replacer(match):
            var_name = match.group(1).strip()
            captured = match.group(2)
            ctx[var_name] = captured.strip()
            return ''
        content = re.sub(r'\{%\s*capture\s+(\w+)\s*%\}(.*?)\{%\s*endcapture\s*%\}', capture_replacer, content, flags=re.DOTALL)
        
        # Process assign
        def assign_replacer(match):
            var_name = match.group(1).strip()
            value = match.group(2).strip()
            ctx[var_name] = self.resolve_var(value, ctx) or value.strip('"\'')
            return ''
        content = re.sub(r'\{%\s*assign\s+(\w+)\s*=\s*(.+?)\s*%\}', assign_replacer, content)
        
        # Process for loops
        def for_replacer(match):
            var_name = match.group(1).strip()
            collection_expr = match.group(2).strip()
            loop_body = match.group(3)
            
            items = []
            if '|' in collection_expr:
                parts = collection_expr.split('|')
                collection_name = parts[0].strip()
                for part in parts[1:]:
                    part = part.strip()
                    if part.startswith('split:'):
                        sep = part[6:].strip().strip('"\'')
                        raw = self.resolve_var(collection_name, ctx)
                        if isinstance(raw, str):
                            items = raw.split(sep)
            else:
                items = self.resolve_var(collection_expr, ctx) or []
            
            if not isinstance(items, list):
                items = []
            
            result = []
            for i, item in enumerate(items):
                item_ctx = dict(ctx)
                item_ctx[var_name] = item
                item_ctx['forloop'] = {'index': i+1, 'first': i==0, 'last': i==len(items)-1}
                result.append(self.process_liquid(loop_body, item_ctx))
            
            return ''.join(result)
        
        content = re.sub(r'\{%\s*for\s+(\w+)\s+in\s+(.+?)\s*%\}(.*?)\{%\s*endfor\s*%\}', for_replacer, content, flags=re.DOTALL)
        
        # Process if statements with else
        def if_else_replacer(match):
            condition = match.group(1).strip()
            if_body = match.group(2)
            else_body = match.group(3) if match.group(3) else ''
            if self.evaluate_condition(condition, ctx):
                return self.process_liquid(if_body, ctx)
            else:
                return self.process_liquid(else_body, ctx) if else_body else ''
        
        content = re.sub(r'\{%\s*if\s+(.*?)\s*%\}(.*?)\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}', if_else_replacer, content, flags=re.DOTALL)
        
        # Process if without else
        def if_replacer(match):
            condition = match.group(1).strip()
            if_body = match.group(2)
            if self.evaluate_condition(condition, ctx):
                return self.process_liquid(if_body, ctx)
            return ''
        
        content = re.sub(r'\{%\s*if\s+(.*?)\s*%\}(.*?)\{%\s*endif\s*%\}', if_replacer, content, flags=re.DOTALL)
        
        # Process variables {{ var }}
        def var_replacer(match):
            expr = match.group(1).strip()
            result = self.resolve_var(expr, ctx)
            return str(result) if result is not None else ''
        
        content = re.sub(r'\{\{\s*(.+?)\s*\}\}\}', var_replacer, content)
        content = re.sub(r'\{\{\s*(.+?)\s*\}\}', var_replacer, content)
        
        return content
    
    def resolve_var(self, expr, ctx):
        expr = expr.strip()
        # Handle quoted string literals directly
        if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]
        
        if '|' in expr:
            parts = expr.split('|')
            value = self.resolve_var(parts[0].strip(), ctx)
            for filter_expr in parts[1:]:
                filter_expr = filter_expr.strip()
                if filter_expr.startswith('default:'):
                    default_val = filter_expr[8:].strip().strip('"\'')
                    if not value or value == '':
                        value = default_val
                elif filter_expr == 'money_with_currency':
                    value = f'${float(value)/100:.2f} USD' if value else '$0.00'
                elif filter_expr == 'date':
                    from datetime import datetime
                    value = datetime.now().strftime('%Y')
                elif filter_expr.startswith('split:'):
                    sep = filter_expr[6:].strip().strip('"\'')
                    if isinstance(value, str):
                        value = value.split(sep)
                elif filter_expr == 'size':
                    value = len(value) if hasattr(value, '__len__') else 0
                elif filter_expr == 'asset_url':
                    value = f'/assets/{value}'
                elif filter_expr.startswith('replace:'):
                    args = filter_expr[8:].strip()
                    # replace: '.', '-'
                    arg_match = re.match(r"(.+),\s*(.+)", args)
                    if arg_match:
                        old = arg_match.group(1).strip().strip("'\"")
                        new = arg_match.group(2).strip().strip("'\"")
                        if isinstance(value, str):
                            value = value.replace(old, new)
            return value
        
        if '.' in expr:
            parts = expr.split('.')
            current = ctx
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                elif isinstance(current, list) and part.isdigit():
                    current = current[int(part)] if int(part) < len(current) else None
                else:
                    return None
            return current
        
        return ctx.get(expr)
    
    def evaluate_condition(self, condition, ctx):
        condition = condition.strip()
        if ' and ' in condition:
            parts = condition.split(' and ')
            return all(self.evaluate_condition(p.strip(), ctx) for p in parts)
        if ' > ' in condition:
            parts = condition.split(' > ')
            left = self.resolve_var(parts[0].strip(), ctx) or 0
            right = int(parts[1].strip())
            return (left if isinstance(left, int) else 0) > right
        if ' == ' in condition:
            parts = condition.split(' == ')
            left = self.resolve_var(parts[0].strip(), ctx)
            right = parts[1].strip().strip('"\'')
            return str(left) == right
        value = self.resolve_var(condition, ctx)
        if isinstance(value, bool): return value
        if isinstance(value, int): return value > 0
        if isinstance(value, list): return len(value) > 0
        return bool(value)


renderer = LiquidRenderer(BASE)

@app.route('/')
def home():
    return renderer.render('index')

@app.route('/<path:page_path>.html')
def page(page_path):
    path_map = {
        'index': 'index',
        'sample-kit': 'product',
        'diy-test-kit': 'product',
        'project-estimate': 'page.project-estimate',
        'dealer-program': 'page.dealer-program',
        'installation-guide': 'page.installation-guide',
        'faq': 'page.faq',
        'shipping-returns': 'page.shipping-returns',
        'about': 'page.about',
        'contact': 'page.contact',
        'cart': 'cart',
        'checkout': 'checkout',
        'patio-landing': 'page.patio-landing',
        'pool-deck-landing': 'page.pool-deck-landing',
        'garden-path-landing': 'page.garden-path-landing',
    }
    template = path_map.get(page_path, 'index')
    return renderer.render(template)

@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory(os.path.join(BASE, 'assets'), filename)

if __name__ == '__main__':
    print('==============================================')
    print('TerraBond Outdoor v2 - Shopify Theme Preview')
    print('==============================================')
    print('Open: http://localhost:9999/')
    print('Press Ctrl+C to stop')
    print('==============================================')
    app.run(host='0.0.0.0', port=9999, debug=False)
