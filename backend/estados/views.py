from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from users.models import CatalogoEstados

@api_view(['GET'])
@permission_classes([AllowAny])
def estados_list(request):
    estados = CatalogoEstados.objects.all().values('id_estado', 'nombre_estado')
    return Response(list(estados))