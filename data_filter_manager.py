class DataFilterManager:
    """Kullanıcının yetkisine ve organizasyonuna göre verileri filtreler"""
    
    def __init__(self, current_user):
        self.current_user = current_user # dict: {id, organization_id, role}
        
    def filter_machines(self, all_machines):
        """Sadece kullanıcının organizasyonuna ait tezgahları döndürür"""
        if self.current_user['role'] == 'super_admin':
            return all_machines
            
        return [m for m in all_machines if m.get('organization_id') == self.current_user['organization_id']]
        
    def can_edit(self):
        """Kullanıcının düzenleme yetkisi olup olmadığını kontrol eder"""
        return self.current_user['role'] in ['admin', 'editor']

if __name__ == "__main__":
    user = {'id': 1, 'organization_id': 10, 'role': 'editor'}
    manager = DataFilterManager(user)
    
    machines = [
        {'id': 1, 'name': 'Tezgah A', 'organization_id': 10},
        {'id': 2, 'name': 'Tezgah B', 'organization_id': 11}
    ]
    
    filtered = manager.filter_machines(machines)
    print(f"Filtrelenmiş Tezgah Sayısı: {len(filtered)}") # Beklenen: 1
    print(f"Düzenleme Yetkisi: {manager.can_edit()}") # Beklenen: True
