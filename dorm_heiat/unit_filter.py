from collections import defaultdict

from .models import Unit


class UnitTree:
    def __init__(self):
        self.units = list(Unit.objects.select_related('unit_type', 'parent'))
        self.children = defaultdict(list)
        for unit in self.units:
            if unit.active:
                self.children[unit.parent_id].append(unit)
        self.options = []
        self.active_ids = set()
        pending = [(unit, 0) for unit in reversed(self.children[None])]
        while pending:
            unit, depth = pending.pop()
            if unit.pk in self.active_ids:
                continue
            self.active_ids.add(unit.pk)
            self.options.append({
                'id': str(unit.pk), 'label': '— ' * depth + str(unit), 'menu_label': '— ' * depth + unit.name,
            })
            pending.extend((child, depth + 1) for child in reversed(self.children[unit.pk]))

    def descendants(self, root):
        if root not in self.active_ids:
            return set()
        found = set()
        pending = [root]
        while pending:
            unit_id = pending.pop()
            if unit_id not in found:
                found.add(unit_id)
                pending.extend(child.pk for child in self.children[unit_id])
        return found


class UnitFilter:
    def __init__(self, request):
        self.tree = UnitTree()
        self.selected = request.GET.get('unit', '')
        self.options = self.tree.options
        self.ids = None
        if self.selected and self.selected != 'public':
            unit_id = next((int(option['id']) for option in self.options if option['id'] == self.selected), None)
            self.ids = self.tree.descendants(unit_id)
            if not self.ids:
                self.selected = ''

    def apply(self, queryset):
        if self.selected == 'public':
            return queryset.filter(is_public=True)
        if self.ids is not None:
            return queryset.filter(units__in=self.ids).distinct()
        return queryset

    @property
    def query(self):
        return f'?unit={self.selected}' if self.selected else ''


def unit_filter(request):
    if not hasattr(request, '_content_unit_filter'):
        request._content_unit_filter = UnitFilter(request)
    return request._content_unit_filter
