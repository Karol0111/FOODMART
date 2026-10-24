def cart_context(request):
    """
    Context processor to provide cart item count and summary on every page.
    """
    cart = request.session.get('cart', {})
    cart_count = 0
    cart_total = 0.0

    for item_id, item_data in cart.items():
        qty = int(item_data.get('quantity', 1))
        price = float(item_data.get('price', 0.0))
        cart_count += qty
        cart_total += qty * price

    return {
        'cart_count': cart_count,
        'cart_total': round(cart_total, 2),
    }
