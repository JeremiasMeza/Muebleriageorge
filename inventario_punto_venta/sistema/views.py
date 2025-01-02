from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto, Categoria
from django.db.models import Q
from .forms import ProductoForm
from django.http import JsonResponse
from .models import Venta, DetalleVenta
import json
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Sum
from datetime import datetime
from django.utils.timezone import now
from django.views.generic import ListView
from django.template.loader import render_to_string
from django.http import HttpResponse








  # Asegúrate de que el modelo Venta esté correctamente importado









def home(request):
    return render(request, 'sistema/home.html')


def lista_productos(request):
    buscar = request.GET.get('buscar', '')
    codigo_barra = request.GET.get('codigo_barra', '')
    filtro = request.GET.get('filtro', '')
    orden = request.GET.get('orden', '')

    productos = Producto.objects.all()

    # Filtrar por búsqueda (nombre o descripción)
    if buscar:
        productos = productos.filter(
            Q(nombre__icontains=buscar) | Q(descripcion__icontains=buscar)
        )
    
    # Filtrar por código de barra
    if codigo_barra:
        productos = productos.filter(codigo_barra__icontains=codigo_barra)
    
    # Filtrar por cantidad
    if filtro == 'disponible':
        productos = productos.filter(cantidad__gt=0)
    elif filtro == 'agotado':
        productos = productos.filter(cantidad=0)
    
    # Ordenar por precio
    if orden == 'asc':
        productos = productos.order_by('precio')
    elif orden == 'desc':
        productos = productos.order_by('-precio')

    return render(request, 'sistema/productos.html', {'productos': productos})





def agregar_producto(request):
    if request.method == 'POST':
        # Obtenemos los datos del formulario
        nombre = request.POST['nombre']
        codigo_barra = request.POST['codigo_barra']
        descripcion = request.POST.get('descripcion', '')
        precio = request.POST['precio']
        cantidad = request.POST['cantidad']
        categoria_id = request.POST['categoria']
        imagen = request.FILES.get('imagen')  # Captura el archivo de la imagen

        # Comprobamos si ya existe un producto con el mismo nombre o código de barra
        if Producto.objects.filter(nombre=nombre).exists():
            messages.warning(request, f"El producto con el nombre '{nombre}' ya existe.")
            return redirect('agregar_producto')

        if Producto.objects.filter(codigo_barra=codigo_barra).exists():
            messages.warning(request, f"El producto con el código de barra '{codigo_barra}' ya existe.")
            return redirect('agregar_producto')

        # Si no existen duplicados, procedemos a guardar el producto
        try:
            categoria = Categoria.objects.get(id=categoria_id) if categoria_id else None
            producto = Producto(
                nombre=nombre,
                codigo_barra=codigo_barra,
                descripcion=descripcion,
                precio=precio,
                cantidad=cantidad,
                categoria=categoria,
                imagen=imagen
            )
            producto.save()
            messages.success(request, f"Producto '{nombre}' agregado correctamente.")
            return redirect('lista_productos')

        except IntegrityError:
            messages.error(request, "Hubo un error al intentar guardar el producto.")
            return redirect('agregar_producto')

    categorias = Categoria.objects.all()
    return render(request, 'sistema/agregar_producto.html', {'categorias': categorias})


def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('lista_productos')  # Cambia 'listar_productos' por el nombre de tu vista de listado
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'sistema/editar_producto.html', {'form': form, 'producto': producto})



def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == 'POST':
        # Verificar si el producto está siendo utilizado en ventas
        ventas = DetalleVenta.objects.filter(producto=producto)

        if ventas.exists():
            # Si el producto tiene ventas asociadas, mostramos un mensaje de advertencia
            messages.warning(request, f"No se puede eliminar el producto '{producto.nombre}' porque tiene ventas asociadas.")
            return redirect('lista_productos')  # Redirigir a la lista de productos

        # Si no tiene ventas asociadas, proceder con la eliminación
        producto.delete()
        messages.success(request, f"El producto '{producto.nombre}' ha sido eliminado correctamente.")
        return redirect('lista_productos')  # Redirigir a la lista de productos

    return render(request, 'sistema/eliminar_producto.html', {'producto': producto})

# Categorias

def lista_categorias(request):
    if request.method == 'POST':
        # Agregar una nueva categoría
        nombre = request.POST.get('nombre')

        if nombre:
            Categoria.objects.create(nombre=nombre)
            return redirect('lista_categorias')

    categorias = Categoria.objects.all()
    return render(request, 'sistema/categorias.html', {'categorias': categorias})

def eliminar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    categoria.delete()
    return redirect('lista_categorias')

def editar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)

    if request.method == 'POST':
        categoria.nombre = request.POST.get('nombre', categoria.nombre)
        categoria.save()
        return redirect('lista_categorias')

    return render(request, 'sistema/editar_categoria.html', {'categoria': categoria})

# punto de venta




from django.shortcuts import render
from django.http import JsonResponse
from .models import Producto, Venta, DetalleVenta
import json

def punto_de_venta(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            carrito = data.get('carrito', [])
            cliente = data.get('cliente', '')
            rut = data.get('rut', '')  # Obtén el Rut del cliente
            total = 0

            if not carrito:
                return JsonResponse({'error': 'El carrito está vacío.'}, status=400)

            # Crear la venta
            venta = Venta(cliente=cliente, rut=rut, total=0)  # Asigna el rut
            venta.save()

            for item in carrito:
                producto_id = item.get('id')
                if not producto_id or not str(producto_id).isdigit():
                    return JsonResponse({'error': 'El ID del producto no es válido.'}, status=400)

                try:
                    producto = Producto.objects.get(id=producto_id)
                except Producto.DoesNotExist:
                    return JsonResponse({'error': f"Producto con ID {producto_id} no encontrado."}, status=404)

                cantidad = int(item.get('cantidad', 0))
                if producto.cantidad >= cantidad:
                    producto.cantidad -= cantidad
                    producto.save()

                    subtotal = producto.precio * cantidad
                    total += subtotal

                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        subtotal=subtotal
                    )
                else:
                    return JsonResponse({'error': f"No hay suficiente stock de {producto.nombre}"}, status=400)

            # Actualizar el total de la venta
            venta.total = total
            venta.save()

            return JsonResponse({'success': True, 'venta_id': venta.id})
        except Exception as e:
            print(f"Error procesando la venta: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    # Recuperar los filtros de la URL (GET)
    nombre = request.GET.get('nombre', '')
    precio_min = request.GET.get('precio_min', '')
    precio_max = request.GET.get('precio_max', '')
    codigo_barra = request.GET.get('codigo_barra', '')
    orden = request.GET.get('orden', '')  # Nuevo parámetro para ordenar

    # Filtrar productos
    productos = Producto.objects.all()

    if nombre:
        productos = productos.filter(nombre__icontains=nombre)
    if precio_min:
        productos = productos.filter(precio__gte=precio_min)
    if precio_max:
        productos = productos.filter(precio__lte=precio_max)
    if codigo_barra:
        productos = productos.filter(codigo_barra__icontains=codigo_barra)

    # Ordenar productos
    if orden in ['asc', 'desc']:
        productos = productos.order_by('precio' if orden == 'asc' else '-precio')

    # Renderizar la página
    return render(request, 'sistema/punto_de_venta.html', {
        'productos': productos,
    })


def calcular_subtotal(self):
    return self.producto.precio * self.cantidad



# dashboard

def dashboard(request):
    fecha_actual = now()
    
    # Filtrar las ventas del mes actual
    ventas_mes = Venta.objects.filter(fecha__year=fecha_actual.year, fecha__month=fecha_actual.month)

    # Calcular el total de ventas
    total_ventas = sum(venta.total for venta in ventas_mes)

    # Verificar si total_ventas es correcto
    print(f'Total Ventas del Mes: {total_ventas}')  # Esto es solo para depurar en la consola

    # Pasar el total de ventas al contexto
    context = {
        'total_ventas': total_ventas,
    }

    return render(request, 'sistema/dashboard.html', context)



def reportes(request):
    return render(request, 'sistema/reportes.html')



def ventas_generales(request):
    # Búsqueda por cliente, producto o fecha
    search_query = request.GET.get('search', '')
    ventas = Venta.objects.prefetch_related('detalles__producto')

    if search_query:
        ventas = ventas.filter(
            Q(cliente__icontains=search_query) |
            Q(detalles__producto__nombre__icontains=search_query) |
            Q(fecha__icontains=search_query)
        ).distinct()

    context = {
        'ventas': ventas,
        'search_query': search_query,
    }
    return render(request, 'sistema/ventas_generales.html', context)

def eliminar_venta(request, venta_id):
    if request.method == 'POST':
        venta = get_object_or_404(Venta, id=venta_id)
        venta.delete()
        return redirect('ventas_generales')  # Redirige al listado de ventas después de eliminarla
    return redirect('ventas_generales')
# graficos

def ventas_graficos(request):
    return render(request, 'sistema/ventas_graficos.html')

from django.db.models import Sum
from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime
from .models import Venta  # Asegúrate de que el modelo Venta esté correctamente importado

def get_ventas_por_mes(request, periodo):
    # Obtener el año actual
    año_actual = datetime.now().year
    
    # Filtrar todas las ventas para el año actual
    ventas = Venta.objects.filter(fecha__year=año_actual)
    
    # Crear una lista de 12 ceros para representar los 12 meses
    ventas_por_mes = [0] * 12
    
    # Recorrer todos los meses (1 a 12)
    for mes in range(1, 13):
        # Filtrar las ventas de cada mes específico
        ventas_mes = ventas.filter(fecha__month=mes)
        
        # Obtener el total de ventas para ese mes
        total_ventas_mes = ventas_mes.aggregate(total=Sum('total'))['total'] or 0
        
        # Almacenar el total de ventas en el mes correspondiente (índice mes - 1)
        ventas_por_mes[mes - 1] = total_ventas_mes
    
    # Nombres de los meses
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    
    # Devolver los datos como respuesta JSON
    return JsonResponse({
        'labels': meses,  # Los nombres de los meses
        'values': ventas_por_mes  # Las ventas totales de cada mes
    })



