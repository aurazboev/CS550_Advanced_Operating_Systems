import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.Scanner;

public class Client {
    private static final int CLIENT_SERVER_PORT = 9877;

    public static void main(String[] args) {
        String hostname = "192.168.64.3";
        int port = 9876;

        new ClientServerThread(CLIENT_SERVER_PORT).start();

        try (Socket socket = new Socket(hostname, port); BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream())); PrintWriter writer = new PrintWriter(new OutputStreamWriter(socket.getOutputStream()), true); Scanner scanner = new Scanner(System.in)) {

            File folder = new File("./files");
            File[] listOfFiles = folder.listFiles();

            if (listOfFiles != null) {
                for (File file: listOfFiles) {
                    if (file.isFile()) {
                        writer.println("register");
                        writer.println(file.getName());
                        System.out.println("Server responded: " + reader.readLine());
                    }
                }
            }

            long startTime = System.currentTimeMillis();
            for (int i = 1; i <= 1000; i++) {
                String fileName = i + "K.txt";
                System.out.println("Searching for file: " + fileName);

                writer.println("search " + fileName);
                String response = reader.readLine();
                System.out.println("Server responded: " + response);

                if (response.contains("IPs containing")) {
                    String ip = extractFirstIP(response);
                    if (ip != null) {
                        System.out.println("Obtaining file from IP: " + ip);
                        obtain(ip, CLIENT_SERVER_PORT, fileName); // Assuming CLIENT_LISTENING_PORT is defined somewhere in your code
                    }
                }


            }
            long endTime = System.currentTimeMillis();
            System.out.println("Total execution time: " + (double)(endTime - startTime)/1000 + " seconds");
            System.out.println("Exiting...");
            socket.close();

        } catch (IOException ex) {
            System.out.println("Client exception: " + ex.getMessage());
            ex.printStackTrace();
        }
    }

    private static String extractFirstIP(String response) {
        int startIndex = response.indexOf('[');
        int endIndex = response.indexOf(']');

        if (startIndex != -1 && endIndex != -1 && startIndex < endIndex) {
            String ipsString = response.substring(startIndex + 1, endIndex); // Extract the substring between [ and ]
            String[] ips = ipsString.split(","); // Split the substring by , to get the array of IPs

            if (ips.length > 0) {
                return ips[0].trim(); // Return the first IP after trimming any leading and trailing whitespaces
            }
        }

        return null;
    }

    public static void obtain(String ip, int port, String fileName) {
        try (Socket socket = new Socket(ip, port); DataInputStream in = new DataInputStream(socket.getInputStream()); DataOutputStream out = new DataOutputStream(socket.getOutputStream())) {

            out.writeUTF(fileName);
            System.out.println("Connected to " + ip + " at port " + port + " to get " + fileName);

            long fileLength = in .readLong();
            if (fileLength < 0) {
                System.out.println("File not found on the server.");
                return;
            }

            File receivedFile = new File("files/" + fileName);
            try (FileOutputStream fileOut = new FileOutputStream(receivedFile)) {
                byte[] buffer = new byte[4096];
                long remaining = fileLength;
                int read;

                while ((read = in .read(buffer, 0, (int) Math.min(buffer.length, remaining))) > 0) {
                    fileOut.write(buffer, 0, read);
                    remaining -= read;
                }
            }

            System.out.println("File received and saved to: " + receivedFile.getAbsolutePath());
        } catch (IOException e) {
            System.out.println("Error obtaining file: " + e.getMessage());
        }
    }



    public static class ClientServerThread extends Thread {
        int port;

        public ClientServerThread(int port) {
            this.port = port;
        }

        @Override
        public void run() {
            try (ServerSocket serverSocket = new ServerSocket(port)) {
                while (true) {
                    Socket socket = serverSocket.accept();
                    new FileHandler(socket).start();
                }
            } catch (IOException e) {
                System.out.println("Exception in ClientServerThread: " + e.getMessage());
            }
        }
    }

    public static class FileHandler extends Thread {
        Socket socket;

        public FileHandler(Socket socket) {
            this.socket = socket;
        }
        @Override
        public void run() {
            try {
                DataInputStream in = new DataInputStream(socket.getInputStream());
                DataOutputStream out = new DataOutputStream(socket.getOutputStream());

                String fileName = in .readUTF();

                File file = new File("files/" + fileName);
                if (file.exists() && !file.isDirectory()) {
                    out.writeLong(file.length());
                    try (FileInputStream fileIn = new FileInputStream(file)) {
                        byte[] buffer = new byte[4096];
                        int read;
                        while ((read = fileIn.read(buffer)) != -1) {
                            out.write(buffer, 0, read);
                        }
                    }
                } else {
                    out.writeLong(-1);
                }
            } catch (IOException e) {
                System.out.println("Error in FileHandler: " + e.getMessage());
            } finally {
                try {
                    socket.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }

    }

}