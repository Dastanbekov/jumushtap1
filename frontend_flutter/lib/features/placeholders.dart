import 'package:flutter/material.dart';

class OrdersListScreen extends StatelessWidget {
  const OrdersListScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(appBar: AppBar(title: const Text('Orders')), body: const Center(child: Text('Orders List')));
}

class DealsListScreen extends StatelessWidget {
  const DealsListScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(appBar: AppBar(title: const Text('Deals')), body: const Center(child: Text('Deals List')));
}

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(appBar: AppBar(title: const Text('Profile')), body: const Center(child: Text('Profile')));
}
