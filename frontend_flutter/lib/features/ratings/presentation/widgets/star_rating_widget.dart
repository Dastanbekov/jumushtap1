import 'package:flutter/material.dart';

class StarRating extends StatelessWidget {
  final double rating;
  final int count;
  final double size;
  final Color color;
  final Function(double)? onRatingChanged;

  const StarRating({
    super.key,
    required this.rating,
    this.count = 5,
    this.size = 24,
    this.color = Colors.amber,
    this.onRatingChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(count, (index) {
        IconData icon;
        if (index >= rating) {
          icon = Icons.star_border;
        } else if (index > rating - 1 && index < rating) {
          icon = Icons.star_half;
        } else {
          icon = Icons.star;
        }
        
        return GestureDetector(
          onTap: onRatingChanged != null ? () => onRatingChanged!(index + 1.0) : null,
          child: Icon(icon, size: size, color: color),
        );
      }),
    );
  }
}
