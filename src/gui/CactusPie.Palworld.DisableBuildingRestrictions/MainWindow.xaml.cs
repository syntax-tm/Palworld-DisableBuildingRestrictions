using System;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using CactusPie.Palworld.DisableBuildingRestrictions.Modules;
using Memory;

namespace CactusPie.Palworld.DisableBuildingRestrictions
{
    public partial class MainWindow
    {
        private const string PROCESS_NAME = @"Palworld-Win64-Shipping";

        private static readonly Mem GameMemory = new();

        private Task _gameProcessSearchingTask;
        private Task _gameProcessExitWaitingTask;
        private readonly ModuleControl[] _moduleControls;

        public MainWindow()
        {
            _moduleControls =
            [
                new(new NoSnappingModule(this)),
                new(new OverlappingBasesModule(this)),
                new(new OverlappingBuildingsModule(this)),
                new(new WaterBuildingModule(this)),
                new(new BuildingInMidAirModule(this)),
                new(new BuildingCloseToPalboxModule(this))
            ];

            InitializeComponent();
        }

        protected override void OnInitialized(EventArgs e)
        {
            base.OnInitialized(e);

            foreach (var module in _moduleControls)
            {
                StackPanelModules.Children.Add(module);
            }

            _gameProcessSearchingTask = WaitForGameProcess();
        }

        private async Task WaitForGameProcess()
        {
            if (_gameProcessSearchingTask != null) return;

            while (true)
            {
                var procs = Process.GetProcessesByName(PROCESS_NAME);

                if (!procs.Any())
                {
                    await Task.Delay(1000);
                    continue;
                }

                var gameProc = procs.First();
                var opened = GameMemory.OpenProcess(gameProc.Id);

                if (!opened || GameMemory.mProc.Process.HasExited)
                {
                    await Task.Delay(1000);
                    continue;
                }

                break;
            }

            Dispatcher.Invoke(() =>
            {
                LabelWaitingForProcess.Content = $"Initializing (0/{_moduleControls.Length})";
            });

            for (var index = 0; index < _moduleControls.Length; index++)
            {
                var module = _moduleControls[index];
                await module.InitializeModule(GameMemory).ConfigureAwait(false);

                var indexTmp = index;
                Dispatcher.Invoke(() =>
                {
                    LabelWaitingForProcess.Content = $"Initializing ({indexTmp+1}/{_moduleControls.Length})";
                });
            }

            Dispatcher.Invoke(() =>
            {
                LabelWaitingForProcess.Visibility = Visibility.Collapsed;
                StackPanelModules.Visibility = Visibility.Visible;
            });

            _gameProcessSearchingTask = null;
            _gameProcessExitWaitingTask = WaitForGameProcessToExit();
        }

        private async Task WaitForGameProcessToExit()
        {
            if (_gameProcessExitWaitingTask != null) return;

            while (true)
            {
                if (GameMemory.mProc.Process.HasExited) break;

                await Task.Delay(1000).ConfigureAwait(false);
            }

            Dispatcher.Invoke(() =>
            {
                LabelWaitingForProcess.Content = $"Waiting for the game to be running...";
            });

            Dispatcher.Invoke(() =>
            {
                StackPanelModules.Visibility = Visibility.Collapsed;
                LabelWaitingForProcess.Visibility = Visibility.Visible;
            });

            Array.ForEach(_moduleControls, mc => mc.OnGameProcessExited());

            _gameProcessExitWaitingTask = null;
            _gameProcessSearchingTask = WaitForGameProcess();
        }
    }
}