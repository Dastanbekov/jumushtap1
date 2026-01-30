class TokenModel {
  final String access;
  final String refresh;

  TokenModel({required this.access, required this.refresh});

  // Фабрика для создания объекта из JSON
  factory TokenModel.fromJson(Map<String, dynamic> json) {
    return TokenModel(
      access: json['access'],
      refresh: json['refresh'],
    );
  }
}