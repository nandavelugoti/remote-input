// import 'dart:ffi';

import 'dart:convert';
import 'dart:ffi';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:logger/logger.dart';

void main() {
  runApp(const MyApp());
}

class HIDClient {
  static final HIDClient _singleton = HIDClient._internal();
  final List<String> _sendBuffer = List.empty(growable: true);
  final logger = Logger();

  bool _connAlive = false;
  late Socket _socket;

  factory HIDClient() {
    return _singleton;
  }

  HIDClient._internal();

  void _connect() {
    Socket.connect('127.0.0.1', 12321).then((Socket sock) {
      _socket = sock;
      // sock.listen((data) async {}, onError: (error) {
      //   logger.d('Error in listen: $error');
      // }, onDone: () {
      //   _connAlive = false;
      // });
      _connAlive = true;
      _socket.done.then((value) => _connAlive = false);
    }).catchError((e) {
      logger.d('Unable to connect: $e');
    });
  }

  void send(String data) {
    if (!_connAlive) _connect();

    _sendBuffer.add(data);
    List<int> dataToSend = utf8.encode(_sendBuffer.toString());
    if ((dataToSend.length / sizeOf<Int>()) >= 1024) {
      _socket.add(dataToSend);
      _sendBuffer.clear();
    }
  }
}

class Singleton {
  static final Singleton _singleton = Singleton._internal();

  factory Singleton() {
    return _singleton;
  }

  Singleton._internal();
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'RemoteInput',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const MyHomePage(title: 'Remote Input'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});
  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  double dx = 0.0, dy = 0.0;
  final logger = Logger();

  @override
  Widget build(BuildContext context) {
    // final mediaQuery = MediaQuery.of(context);
    final appBar = AppBar(
      backgroundColor: Theme.of(context).colorScheme.primary,
      title: Text(widget.title),
    );
    const whiteTextStyle = TextStyle(
      color: Colors.white,
    );
    HIDClient hidClient = HIDClient();

    return Scaffold(
      appBar: appBar,
      body: Column(
        // mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          const TextField(
            decoration: InputDecoration(
              border: OutlineInputBorder(),
              hintText: 'Tap here for keyboard',
            ),
          ),
          Expanded(
            child: GestureDetector(
              child: Container(
                color: Theme.of(context).colorScheme.secondary,
                constraints: const BoxConstraints.expand(),
                child: Column(
                  children: [
                    const Text('Remote Trackpad', style: whiteTextStyle),
                    Text('x: $dx', style: whiteTextStyle),
                    Text('y: $dy', style: whiteTextStyle),
                  ],
                ),
              ),
              onPanUpdate: (details) {
                setState(() {
                  dx = details.delta.dx;
                  dy = details.delta.dy;
                });
                Map xy = {'type': 'MOUSE', 'value': '$dx,$dy'};
                hidClient.send(xy.toString());
              },
            ),
          ),
        ],
      ),
    );
  }
}
