from faker.providers import BaseProvider

class NigerianNamesProvider(BaseProvider):
    def nigerian_female_name(self):
        names = [
            'Chioma', 'Ngozi', 'Ifeoma', 'Amaka', 'Ada', 'Chinyere', 
            'Nkechi', 'Uche', 'Chidinma', 'Oluchi', 'Aisha', 'Yetunde',
            'Bukola', 'Yewande', 'Temidayo', 'Omowumi', 'Eniola', 'Funmi'
        ]
        return self.random_element(names)
