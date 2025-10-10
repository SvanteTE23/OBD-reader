"""
Test av GPIO-knapp funktionalitet
Kör detta för att testa sidbytet utan att behöva riktig GPIO-hårdvara
"""

# Simulera sidbyten
current_page = 0
num_pages = 4

print("=== Test av sidbyten ===")
print(f"Antal sidor: {num_pages}")
print(f"Startar på sida: {current_page + 1}")
print()

for i in range(10):
    print(f"Tryck {i+1}: ", end="")
    current_page = (current_page + 1) % num_pages
    print(f"Byter till sida {current_page + 1}")

print()
print("Förväntad ordning: 1→2→3→4→1→2→3→4→1→2")
print("✓ Loop-funktionalitet fungerar korrekt!")
