from dashboard.models import Unidad, GastoUnidad
from datetime import date
from dateutil.relativedelta import relativedelta

def verify():
    print("--- STARTING VERIFICATION ---")
    
    # 1. Test Hologram Calculation
    print("Test 1: Hologram Calculation (2024 Model)")
    u = Unidad(
        nUnidad="TEST-01", 
        placas="ABC-12-34", 
        marca="Nissan", 
        submarca="NP300", 
        modelo_anio=2024,
        capacidad_kg=1000
    )
    u.save()
    print(f"Unidad Created: {u}")
    print(f"Holograma: {u.holograma}")
    
    assert u.holograma == '00', f"Error: Expected '00' but got {u.holograma}"
    print("✅ Hologram logic PASSED")

    # 2. Test Expense Trigger (Seguro)
    print("\nTest 2: Expense Trigger (Seguro)")
    hoy = date.today()
    gasto = GastoUnidad(
        unidad=u,
        fecha=hoy,
        tipo='Seguro',
        detalle='Póliza Anual',
        costo=5000
    )
    gasto.save()
    
    u.refresh_from_db()
    video_vencimiento = u.vencimiento_poliza
    esperado = hoy + relativedelta(years=1)
    
    print(f"Fecha Gasto: {hoy}")
    print(f"Vencimiento Póliza (Updated): {video_vencimiento}")
    
    assert video_vencimiento == esperado, f"Error: Expected {esperado} but got {video_vencimiento}"
    print("✅ Auto-renewal logic PASSED")
    
    print("\n--- VERIFICATION SUCCESSFUL ---")

if __name__ == "__main__":
    try:
        verify()
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
